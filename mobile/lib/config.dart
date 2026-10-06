/// Base URL of the Django API.
///
/// Default is for a real phone over USB, with the port forwarded first:
///   adb reverse tcp:8000 tcp:8000
/// For the Android emulator, run with:
///   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api
/// For a phone on the same Wi-Fi, use your PC's address:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000/api
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000/api',
);

/// Must match MIN_CONFIDENCE in ml/risk/severity.py. Detections below this
/// are shown faded because the server ignores them when scoring.
const double kScoringMinConfidence = 0.30;