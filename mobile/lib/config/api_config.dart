/// Backend API base URL.
///
/// Override at build/run time:
/// `flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000`
///
/// Default `10.0.2.2` is the Android emulator alias for the host machine's localhost.
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
