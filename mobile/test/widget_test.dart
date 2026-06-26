import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fromo/main.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

void main() {
  setUpAll(() async {
    // Supabase must be initialized before the app starts because the router
    // checks auth state via Supabase.instance at build time.
    // Fake credentials are fine here — no real network calls are made in tests.
    await Supabase.initialize(
      url: 'https://example.supabase.co',
      publishableKey: 'test-publishable-key',
    );
  });

  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: FroMoApp()));
    expect(find.byType(FroMoApp), findsOneWidget);
  });
}
