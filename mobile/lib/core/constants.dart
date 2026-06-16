class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator → localhost
  );
}

class SupabaseConfig {
  static const String url = 'https://seqpmxiutifcrbitmajh.supabase.co';
  static const String anonKey =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNlcXBteGl1dGlmY3JiaXRtYWpoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODAyNTYzNTIsImV4cCI6MjA5NTgzMjM1Mn0.0Y-ukDUX7CrTLFVd_ZepZ1Eq0vmdV9IxU0ivkyLk8Cs';
}
