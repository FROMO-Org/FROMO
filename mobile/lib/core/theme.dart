import 'package:flutter/material.dart';

const _teal = Color(0xFF14B8A6);
const _tealDark = Color(0xFF0D9488);

final fromoTheme = ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(seedColor: _teal, primary: _teal),
  appBarTheme: const AppBarTheme(
    backgroundColor: Colors.white,
    foregroundColor: Color(0xFF111827),
    elevation: 0,
    scrolledUnderElevation: 1,
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: Colors.white,
    indicatorColor: _teal.withValues(alpha: 0.15),
    labelTextStyle: WidgetStateProperty.resolveWith((states) {
      if (states.contains(WidgetState.selected)) {
        return const TextStyle(
          color: _teal,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        );
      }
      return const TextStyle(color: Color(0xFF6B7280), fontSize: 12);
    }),
    iconTheme: WidgetStateProperty.resolveWith((states) {
      if (states.contains(WidgetState.selected)) {
        return const IconThemeData(color: _teal);
      }
      return const IconThemeData(color: Color(0xFF6B7280));
    }),
  ),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: _teal,
      foregroundColor: Colors.white,
      minimumSize: const Size(double.infinity, 48),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
    ),
  ),
  chipTheme: ChipThemeData(
    selectedColor: _teal,
    labelStyle: const TextStyle(fontSize: 14),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
  ),
  cardTheme: CardThemeData(
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
      side: BorderSide(color: Colors.black.withValues(alpha: 0.08)),
    ),
    color: Colors.white,
  ),
  extensions: const [FromoColors()],
);

class FromoColors extends ThemeExtension<FromoColors> {
  const FromoColors();
  static const teal = _teal;
  static const tealDark = _tealDark;
  static const gray50 = Color(0xFFF9FAFB);
  static const gray100 = Color(0xFFF3F4F6);
  static const gray200 = Color(0xFFE5E7EB);
  static const gray500 = Color(0xFF6B7280);
  static const gray700 = Color(0xFF374151);
  static const gray900 = Color(0xFF111827);
  static const green600 = Color(0xFF059669);
  static const amber500 = Color(0xFFF59E0B);

  @override
  FromoColors copyWith() => const FromoColors();

  @override
  FromoColors lerp(FromoColors? other, double t) => this;
}
