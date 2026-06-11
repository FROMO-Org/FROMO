import 'package:go_router/go_router.dart';
import '../features/map/map_screen.dart';
import '../features/events/event_detail_screen.dart';
import '../features/bookings/bookings_screen.dart';
import '../features/saved/saved_screen.dart';
import '../features/profile/profile_screen.dart';
import '../shared/widgets/shell.dart';

final router = GoRouter(
  initialLocation: '/map',
  routes: [
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(path: '/map', builder: (_, _) => const MapScreen()),
        GoRoute(path: '/saved', builder: (_, _) => const SavedScreen()),
        GoRoute(path: '/bookings', builder: (_, _) => const BookingsScreen()),
        GoRoute(path: '/profile', builder: (_, _) => const ProfileScreen()),
      ],
    ),
    GoRoute(
      path: '/events/:id',
      builder: (context, state) =>
          EventDetailScreen(eventId: state.pathParameters['id']!),
    ),
  ],
);
