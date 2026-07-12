import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

enum FeedbackVote { up, down }

typedef FeedbackSubmitter =
    Future<void> Function(Map<String, dynamic> payload);
typedef CurrentUserIdReader = String? Function();
typedef NowProvider = DateTime Function();

class FeedbackService {
  FeedbackService(
    SupabaseClient supabase, {
    FeedbackSubmitter? submitter,
    CurrentUserIdReader? currentUserIdReader,
    NowProvider? nowProvider,
  }) : _submitter =
           submitter ??
           ((payload) => supabase.from('feedback').insert(payload)),
       _currentUserIdReader =
           currentUserIdReader ?? (() => supabase.auth.currentUser?.id),
       _nowProvider = nowProvider ?? DateTime.now;

  final FeedbackSubmitter _submitter;
  final CurrentUserIdReader _currentUserIdReader;
  final NowProvider _nowProvider;

  static const _launchCountKey = 'feedback.app_launch_count';
  static const _lastPromptAtKey = 'feedback.last_prompt_at';
  static const _lastDismissedAtKey = 'feedback.last_dismissed_at';
  static const _lastSubmittedAtKey = 'feedback.last_submitted_at';

  static const _minimumLaunchesBeforePrompt = 3;
  static const _dismissCooldown = Duration(days: 7);
  static const _submitCooldown = Duration(days: 30);

  Future<void> recordAppLaunch() async {
    final prefs = await SharedPreferences.getInstance();
    final launches = prefs.getInt(_launchCountKey) ?? 0;
    await prefs.setInt(_launchCountKey, launches + 1);
  }

  Future<bool> shouldPromptForAppFeedback() async {
    if (_currentUserIdReader() == null) return false;

    final prefs = await SharedPreferences.getInstance();
    final launches = prefs.getInt(_launchCountKey) ?? 0;
    if (launches < _minimumLaunchesBeforePrompt) return false;

    final now = _nowProvider();
    final lastSubmittedAt = _readDate(prefs, _lastSubmittedAtKey);
    if (lastSubmittedAt != null &&
        now.difference(lastSubmittedAt) < _submitCooldown) {
      return false;
    }

    final lastDismissedAt = _readDate(prefs, _lastDismissedAtKey);
    if (lastDismissedAt != null &&
        now.difference(lastDismissedAt) < _dismissCooldown) {
      return false;
    }

    return true;
  }

  Future<void> markPromptShown() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_lastPromptAtKey, _nowProvider().toIso8601String());
  }

  Future<void> dismissPrompt() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _lastDismissedAtKey,
      _nowProvider().toIso8601String(),
    );
  }

  Future<void> submitAppFeedback({
    required FeedbackVote vote,
    String? comment,
  }) async {
    final userId = _currentUserIdReader();
    if (userId == null) {
      throw StateError('Cannot submit feedback without a logged-in user');
    }

    await _submitter({
      'user_id': userId,
      'event_id': null,
      'feature': 'app_experience',
      'rating': vote == FeedbackVote.up ? 1 : -1,
      'comment': _normalizeComment(comment),
    });

    final prefs = await SharedPreferences.getInstance();
    final nowIso = _nowProvider().toIso8601String();
    await prefs.setString(_lastSubmittedAtKey, nowIso);
    await prefs.remove(_lastDismissedAtKey);
  }

  DateTime? _readDate(SharedPreferences prefs, String key) {
    final raw = prefs.getString(key);
    if (raw == null || raw.isEmpty) return null;
    return DateTime.tryParse(raw);
  }

  String? _normalizeComment(String? comment) {
    final trimmed = comment?.trim();
    if (trimmed == null || trimmed.isEmpty) return null;
    return trimmed;
  }
}
