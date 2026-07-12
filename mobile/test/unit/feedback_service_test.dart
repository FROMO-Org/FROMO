import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/features/feedback/feedback_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

void main() {
  late DateTime now;
  late FeedbackService service;
  late List<Map<String, dynamic>> submittedPayloads;

  setUpAll(() async {
    SharedPreferences.setMockInitialValues({});
    await Supabase.initialize(
      url: 'https://example.supabase.co',
      publishableKey: 'test-publishable-key',
    );
  });

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    now = DateTime(2026, 7, 10, 12);
    submittedPayloads = [];
    service = FeedbackService(
      Supabase.instance.client,
      submitter: (payload) async {
        submittedPayloads.add(payload);
      },
      currentUserIdReader: () => 'user-1',
      nowProvider: () => now,
    );
  });

  test('does not prompt before minimum launch count', () async {
    await service.recordAppLaunch();
    await service.recordAppLaunch();

    expect(await service.shouldPromptForAppFeedback(), isFalse);
  });

  test('does not prompt within 30 days after submission', () async {
    for (var i = 0; i < 3; i++) {
      await service.recordAppLaunch();
    }

    await service.submitAppFeedback(vote: FeedbackVote.up);

    expect(await service.shouldPromptForAppFeedback(), isFalse);
  });

  test('does not prompt within 7 days after dismissal', () async {
    for (var i = 0; i < 3; i++) {
      await service.recordAppLaunch();
    }

    await service.dismissPrompt();
    expect(await service.shouldPromptForAppFeedback(), isFalse);
  });

  test('submits normalized payload and clears dismissal cooldown', () async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      'feedback.last_dismissed_at',
      now.subtract(const Duration(days: 1)).toIso8601String(),
    );

    await service.submitAppFeedback(
      vote: FeedbackVote.down,
      comment: '  Needs better recommendations  ',
    );

    expect(submittedPayloads, hasLength(1));
    expect(submittedPayloads.single, {
      'user_id': 'user-1',
      'event_id': null,
      'feature': 'app_experience',
      'rating': -1,
      'comment': 'Needs better recommendations',
    });
    expect(prefs.getString('feedback.last_dismissed_at'), isNull);
  });
}
