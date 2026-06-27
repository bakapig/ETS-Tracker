/// Backend API base URL.
///
/// Override at build/run time:
/// `flutter run --dart-define=API_BASE_URL=https://api.example.com --dart-define=API_KEY=your-key`
///
/// Default `10.0.2.2` is the Android emulator alias for the host machine's localhost.
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// Sent as `X-API-Key` when non-empty (must match server API_KEY secret).
  static const String apiKey = String.fromEnvironment('API_KEY', defaultValue: '');
}
