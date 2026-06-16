import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'api_client.dart';

final supabase = Supabase.instance.client;

// Current auth session — rebuilds whenever login/logout happens
final authStateProvider = StreamProvider<AuthState>((ref) {
  return supabase.auth.onAuthStateChange;
});

// Convenience: is there a logged-in user right now?
final currentUserProvider = Provider<User?>((ref) {
  return supabase.auth.currentUser;
});

// Auth actions (login, register, logout)
final authActionsProvider = Provider<AuthActions>((ref) {
  return AuthActions(ref);
});

class AuthActions {
  final Ref _ref;
  AuthActions(this._ref);

  Future<void> signIn(String email, String password) async {
    final res = await supabase.auth.signInWithPassword(
      email: email,
      password: password,
    );
    // Store the JWT so our API client sends it on every request
    if (res.session != null) {
      await _ref.read(apiClientProvider).setToken(res.session!.accessToken);
      await _ensureProfile(res.user!);
    }
  }

  Future<void> signUp(String email, String password, String fullName) async {
    final res = await supabase.auth.signUp(
      email: email,
      password: password,
      data: {'full_name': fullName},
    );
    if (res.session != null) {
      await _ref.read(apiClientProvider).setToken(res.session!.accessToken);
      await _ensureProfile(res.user!);
    }
  }

  Future<void> signOut() async {
    await supabase.auth.signOut();
    await _ref.read(apiClientProvider).clearToken();
  }

  // Call POST /profiles/me after first login — backend creates the row
  Future<void> _ensureProfile(User user) async {
    try {
      final api = _ref.read(apiClientProvider);
      // Try to GET first; only POST if it doesn't exist yet
      try {
        await api.get('/profiles/me');
      } catch (_) {
        final name = user.userMetadata?['full_name'] as String? ?? '';
        await api.post('/profiles/me', data: {'full_name': name});
      }
    } catch (_) {
      // Profile creation is best-effort; don't block login
    }
  }
}
