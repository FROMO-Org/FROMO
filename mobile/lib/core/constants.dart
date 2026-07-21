import 'package:flutter/foundation.dart';

class ApiConfig {
  static String get baseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) return envUrl;
    // Web deploys need the public backend; Android emulator uses the host loopback.
    return kIsWeb ? 'https://fromo.onrender.com' : 'http://10.0.2.2:8000';
  }

  static const String orsApiKey = String.fromEnvironment('ORS_API_KEY');
}

class SupabaseConfig {
  static const String url = 'https://seqpmxiutifcrbitmajh.supabase.co';
  static const String anonKey =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNlcXBteGl1dGlmY3JiaXRtYWpoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAyNTYzNTIsImV4cCI6MjA5NTgzMjM1Mn0.0Y-ukDUX7CrTLFVd_ZepZ1Eq0vmdV9IxU0ivkyLk8Cs';
}
