import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/features/bookings/bookings_providers.dart';
import 'package:fromo/features/bookings/bookings_screen.dart';

void main() {
  testWidgets('shows empty state when there are no bookings', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          myBookingsProvider.overrideWith((ref) async => []),
        ],
        child: const MaterialApp(home: BookingsScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('No bookings yet'), findsOneWidget);
    expect(find.text("Book an event and it'll show up here"), findsOneWidget);
  });
}
