import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppShell extends StatelessWidget {
  final Widget child;
  const AppShell({super.key, required this.child});

  static const _tabs = [
    (path: '/map', label: 'Home', icon: Icons.home_outlined, activeIcon: Icons.home),
    (path: '/saved', label: 'Saved', icon: Icons.bookmark_outline, activeIcon: Icons.bookmark),
    (path: '/profile', label: 'Profile', icon: Icons.person_outline, activeIcon: Icons.person),
  ];

  int _indexFor(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    final i = _tabs.indexWhere((t) => location.startsWith(t.path));
    return i < 0 ? 0 : i;
  }

  @override
  Widget build(BuildContext context) {
    final current = _indexFor(context);
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: current,
        onDestinationSelected: (i) => context.go(_tabs[i].path),
        destinations: _tabs
            .map((t) => NavigationDestination(
                  icon: Icon(t.icon),
                  selectedIcon: Icon(t.activeIcon),
                  label: t.label,
                ))
            .toList(),
      ),
    );
  }
}
