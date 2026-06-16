import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/register_screen.dart';
import '../features/map/map_screen.dart';
import '../features/events/event_detail_screen.dart';
import '../features/saved/saved_screen.dart';
import '../features/profile/profile_screen.dart';
import '../shared/widgets/shell.dart';

final router = GoRouter(
  initialLocation: '/map',
  redirect: (context, state) {
    final loggedIn = Supabase.instance.client.auth.currentUser != null;
    final onAuth = state.uri.path == '/login' || state.uri.path == '/register';
    if (!loggedIn && !onAuth) return '/login';
    if (loggedIn && onAuth) return '/map';
    return null;
  },
  routes: [
    // Auth routes (no bottom nav)
    GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
    GoRoute(path: '/register', builder: (_, _) => const RegisterScreen()),

    // Main app (with bottom nav shell)
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(path: '/map', builder: (_, _) => const MapScreen()),
        GoRoute(path: '/saved', builder: (_, _) => const SavedScreen()),
        GoRoute(path: '/profile', builder: (_, _) => const ProfileScreen()),
      ],
    ),

    // Full-screen routes (no bottom nav)
    GoRoute(
      path: '/events/:id',
      builder: (context, state) =>
          EventDetailScreen(eventId: state.pathParameters['id']!),
    ),
  ],
);
