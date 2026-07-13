import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/features/events/event_detail_providers.dart';
import 'package:fromo/features/events/event_detail_screen.dart';

void main() {
  testWidgets('shows error state when detail provider fails', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          eventDetailProvider.overrideWith((ref, arg) async {
            throw Exception('boom');
          }),
          savedEventIdsProvider.overrideWith((ref) async => <String>{}),
        ],
        child: const MaterialApp(
          home: EventDetailScreen(eventId: 'event-1'),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text("Couldn't load this event"), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });
}
