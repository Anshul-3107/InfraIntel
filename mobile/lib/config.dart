/// Base URL of the Django API. Override at run time, for example for a real phone:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000/api
/// 10.0.2.2 is how the Android emulator reaches your computer's localhost.
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000/api',
);

/// Must match MIN_CONFIDENCE in ml/risk/severity.py. Detections below this
/// are shown faded because the server ignores them when scoring.
const double kScoringMinConfidence = 0.30;