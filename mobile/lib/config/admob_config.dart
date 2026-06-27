/// AdMob configuration — override at build/run time with `--dart-define`.
///
/// Banner units (production):
/// `flutter run --dart-define=ADMOB_BANNER_TOP=ca-app-pub-…/… --dart-define=ADMOB_BANNER_BOTTOM=ca-app-pub-…/…`
///
/// App ID is set in `android/gradle.properties` as `ADMOB_APP_ID` (see `gradle.properties.example`).
class AdMobConfig {
  /// Google sample banner — used when slot-specific unit is not configured.
  static const String testBannerId =
      'ca-app-pub-3940256099942544/6300978111';

  static const String _bannerTop = String.fromEnvironment(
    'ADMOB_BANNER_TOP',
    defaultValue: '',
  );

  static const String _bannerBottom = String.fromEnvironment(
    'ADMOB_BANNER_BOTTOM',
    defaultValue: '',
  );

  static String bannerUnitId(String slot) {
    final configured = switch (slot) {
      'top-banner' => _bannerTop,
      'bottom-banner' => _bannerBottom,
      _ => '',
    };
    return configured.isNotEmpty ? configured : testBannerId;
  }

  static bool isProductionUnit(String slot) {
    return switch (slot) {
      'top-banner' => _bannerTop.isNotEmpty,
      'bottom-banner' => _bannerBottom.isNotEmpty,
      _ => false,
    };
  }
}
