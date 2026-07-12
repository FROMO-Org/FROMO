import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:integration_test/integration_test.dart';
import 'package:fromo/shared/widgets/shell.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('bottom navigation moves across tabs', (tester) async {
    final router = GoRouter(
      initialLocation: '/map',
      routes: [
        ShellRoute(
          builder: (_, _, child) => AppShell(child: child),
          routes: [
            GoRoute(
              path: '/map',
              builder: (_, _) => const Scaffold(body: Text('Map Page')),
            ),
            GoRoute(
              path: '/saved',
              builder: (_, _) => const Scaffold(body: Text('Saved Page')),
            ),
            GoRoute(
              path: '/bookings',
              builder: (_, _) => const Scaffold(body: Text('Bookings Page')),
            ),
            GoRoute(
              path: '/profile',
              builder: (_, _) => const Scaffold(body: Text('Profile Page')),
            ),
          ],
        ),
      ],
    );

    await tester.pumpWidget(MaterialApp.router(routerConfig: router));
    await tester.pumpAndSettle();

    expect(find.text('Map Page'), findsOneWidget);

    await tester.tap(find.text('Saved'));
    await tester.pumpAndSettle();
    expect(find.text('Saved Page'), findsOneWidget);

    await tester.tap(find.text('Bookings'));
    await tester.pumpAndSettle();
    expect(find.text('Bookings Page'), findsOneWidget);

    await tester.tap(find.text('Profile'));
    await tester.pumpAndSettle();
    expect(find.text('Profile Page'), findsOneWidget);
  });
}
