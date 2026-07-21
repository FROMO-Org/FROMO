import 'package:flutter/material.dart';

const _paper = Color(0xFF111111);
const _surface = Color(0xFF1C1C1E);
const _ink = Color(0xFFF5F0E8);
const _line = Color(0xFF2C2C2E);
const _muted = Color(0xFF8E8E93);
const _amber = Color(0xFFF5A623);
const _amberPress = Color(0xFFDE9213);
const _amberInk = Color(0xFF231A09);
const _ok = Color(0xFF2E9E6B);
const _danger = Color(0xFFE53935);

final fromoTheme = ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  scaffoldBackgroundColor: _paper,
  colorScheme: ColorScheme.fromSeed(
    brightness: Brightness.dark,
    seedColor: _amber,
    primary: _amber,
    secondary: _ok,
    error: _danger,
    surface: _surface,
    onPrimary: _amberInk,
    onSecondary: _surface,
    onSurface: _ink,
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: _paper,
    foregroundColor: _ink,
    elevation: 0,
    scrolledUnderElevation: 1,
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: _surface,
    indicatorColor: _amber.withValues(alpha: 0.18),
    labelTextStyle: WidgetStateProperty.resolveWith((states) {
      if (states.contains(WidgetState.selected)) {
        return const TextStyle(
          color: _amberInk,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        );
      }
      return const TextStyle(color: _muted, fontSize: 12);
    }),
    iconTheme: WidgetStateProperty.resolveWith((states) {
      if (states.contains(WidgetState.selected)) {
        return const IconThemeData(color: _amberInk);
      }
      return const IconThemeData(color: _muted);
    }),
  ),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: _amber,
      foregroundColor: _amberInk,
      minimumSize: const Size(double.infinity, 48),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
    ),
  ),
  chipTheme: ChipThemeData(
    selectedColor: _amber,
    backgroundColor: _surface,
    labelStyle: const TextStyle(fontSize: 14),
    side: const BorderSide(color: _line),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
  ),
  cardTheme: CardThemeData(
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
      side: const BorderSide(color: _line),
    ),
    color: _surface,
  ),
  extensions: const [FromoColors()],
);

class FromoColors extends ThemeExtension<FromoColors> {
  const FromoColors();
  static const paper = _paper;
  static const surface = _surface;
  static const ink = _ink;
  static const line = _line;
  static const muted = _muted;
  static const amber500 = _amber;
  static const amberPress = _amberPress;
  static const amberInk = _amberInk;
  static const green600 = _ok;
  static const danger = _danger;

  // Legacy aliases kept so existing mobile widgets inherit the web brand color.
  static const teal = _amber;
  static const tealDark = _amberPress;
  static const gray50 = _paper;
  static const gray100 = _surface;
  static const gray200 = _line;
  static const gray500 = _muted;
  static const gray700 = Color(0xFFC9C1B8);
  static const gray900 = _ink;

  @override
  FromoColors copyWith() => const FromoColors();

  @override
  FromoColors lerp(FromoColors? other, double t) => this;
}
