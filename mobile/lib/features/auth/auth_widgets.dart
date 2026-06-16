import 'package:flutter/material.dart';
import '../../core/theme.dart';

class ErrorBanner extends StatelessWidget {
  final String message;
  const ErrorBanner(this.message, {super.key});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFEE2E2),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFDC2626), size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(message, style: const TextStyle(color: Color(0xFFDC2626), fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class AuthLabel extends StatelessWidget {
  final String text;
  const AuthLabel(this.text, {super.key});
  @override
  Widget build(BuildContext context) => Text(
        text,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: FromoColors.gray700,
        ),
      );
}

class FromoLogo extends StatelessWidget {
  const FromoLogo({super.key});
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: FromoColors.teal,
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Icon(Icons.explore, color: Colors.white, size: 26),
        ),
        const SizedBox(width: 10),
        const Text(
          'FROMO',
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w800,
            color: FromoColors.gray900,
            letterSpacing: 1,
          ),
        ),
      ],
    );
  }
}

InputDecoration authInputDeco(String hint) => InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: FromoColors.gray500, fontSize: 14),
      filled: true,
      fillColor: FromoColors.gray50,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: FromoColors.gray200),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: FromoColors.gray200),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: FromoColors.teal, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFDC2626)),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFDC2626), width: 1.5),
      ),
    );
