import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'core/api_client.dart';
import 'core/auth_provider.dart';
import 'core/constants.dart';
import 'core/router.dart';
import 'core/theme.dart';
import 'features/feedback/feedback_providers.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(
    url: SupabaseConfig.url,
    publishableKey: SupabaseConfig.anonKey,
  );
  runApp(const ProviderScope(child: FroMoApp()));
}

class FroMoApp extends ConsumerStatefulWidget {
  const FroMoApp({super.key});

  @override
  ConsumerState<FroMoApp> createState() => _FroMoAppState();
}

class _FroMoAppState extends ConsumerState<FroMoApp> {
  StreamSubscription<AuthState>? _authSub;

  @override
  void initState() {
    super.initState();
    _syncInitialSession();
    unawaited(ref.read(feedbackPromptControllerProvider).recordAppLaunch());
    _authSub = supabase.auth.onAuthStateChange.listen((authState) async {
      final session = authState.session;
      final api = ref.read(apiClientProvider);
      if (session?.accessToken case final token?) {
        await api.setToken(token);
      } else {
        await api.clearToken();
      }
    });
  }

  Future<void> _syncInitialSession() async {
    final session = supabase.auth.currentSession;
    if (!mounted) return;
    final api = ref.read(apiClientProvider);
    if (session?.accessToken case final token?) {
      await api.setToken(token);
    } else {
      await api.clearToken();
    }
  }

  @override
  void dispose() {
    _authSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'FROMO',
      theme: fromoTheme,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
