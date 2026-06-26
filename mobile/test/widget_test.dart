import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fromo/main.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

void main() {
  setUpAll(() async {
    // shared_preferences is not available in the test environment (no real device),
    // so we provide an empty in-memory mock before Supabase.initialize() is called,
    // because Supabase uses SharedPreferences internally to persist auth state.
    SharedPreferences.setMockInitialValues({});

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
