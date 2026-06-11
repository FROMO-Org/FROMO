import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router.dart';
import 'core/theme.dart';

void main() {
  runApp(const ProviderScope(child: FroMoApp()));
}

class FroMoApp extends StatelessWidget {
  const FroMoApp({super.key});

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
