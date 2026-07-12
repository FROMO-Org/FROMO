import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/features/feedback/feedback_prompt.dart';
import 'package:fromo/features/feedback/feedback_service.dart';
import 'dart:async';

void main() {
  Future<Completer<FeedbackVote?>> pumpPrompt(WidgetTester tester) async {
    final completer = Completer<FeedbackVote?>();

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: Center(
              child: ElevatedButton(
                onPressed: () async {
                  completer.complete(await showAppFeedbackPrompt(context));
                },
                child: const Text('Open'),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    return completer;
  }

  testWidgets('returns thumbs up when tapped', (tester) async {
    final result = await pumpPrompt(tester);
    expect(find.text('Thumbs up'), findsOneWidget);

    await tester.tap(find.text('Thumbs up'));
    await tester.pumpAndSettle();

    expect(await result.future, FeedbackVote.up);
  });

  testWidgets('returns thumbs down when tapped', (tester) async {
    final result = await pumpPrompt(tester);

    await tester.tap(find.text('Thumbs down'));
    await tester.pumpAndSettle();

    expect(await result.future, FeedbackVote.down);
  });

  testWidgets('dismisses when maybe later is tapped', (tester) async {
    final result = await pumpPrompt(tester);

    await tester.tap(find.text('Maybe later'));
    await tester.pumpAndSettle();

    expect(await result.future, isNull);
  });
}
