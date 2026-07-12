import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../core/api_client.dart';
import 'feedback_service.dart';

final feedbackServiceProvider = Provider<FeedbackService>((ref) {
  return FeedbackService(
    Supabase.instance.client,
    submitter: (payload) async {
      await ref.read(apiClientProvider).post('/feedback/', data: {
        'event_id': payload['event_id'],
        'feature': payload['feature'],
        'rating': payload['rating'],
        'comment': payload['comment'],
      });
    },
  );
});

final feedbackPromptControllerProvider = Provider<FeedbackPromptController>((
  ref,
) {
  return FeedbackPromptController(ref.read(feedbackServiceProvider));
});

class FeedbackPromptController {
  FeedbackPromptController(this._service);

  final FeedbackService _service;

  Future<void> recordAppLaunch() => _service.recordAppLaunch();

  Future<bool> shouldPrompt() => _service.shouldPromptForAppFeedback();

  Future<void> markPromptShown() => _service.markPromptShown();

  Future<void> dismissPrompt() => _service.dismissPrompt();

  Future<void> submit(FeedbackVote vote, {String? comment}) {
    return _service.submitAppFeedback(vote: vote, comment: comment);
  }
}
