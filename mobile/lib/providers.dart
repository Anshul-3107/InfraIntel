import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_client.dart';
import 'models.dart';

final storageProvider = Provider<FlutterSecureStorage>(
  (ref) => const FlutterSecureStorage(),
);

final apiProvider = Provider<ApiClient>(
  (ref) => ApiClient(ref.watch(storageProvider)),
);

/// Past inspections, newest first. Invalidate after a new upload.
/// Automatic retry is switched off so errors show immediately.
final historyProvider = FutureProvider<List<Inspection>>(
  (ref) => ref.read(apiProvider).listInspections(),
  retry: (_, _) => null,
);

/// All assets with their health, for the map. Invalidate after a new upload.
final assetsProvider = FutureProvider<List<Asset>>(
  (ref) => ref.read(apiProvider).listAssets(),
  retry: (_, _) => null,
);

/// State is the signed-in username, or null when signed out.
class AuthNotifier extends AsyncNotifier<String?> {
  @override
  Future<String?> build() async {
    final api = ref.read(apiProvider);
    if (!await api.hasSession()) return null;
    try {
      return await api.me();
    } catch (_) {
      return null; // network down or session expired: show the login screen
    }
  }

  /// Throws [ApiException] on failure so the login screen can show it.
  Future<void> login(String username, String password) async {
    final api = ref.read(apiProvider);
    await api.login(username, password);
    ref.invalidate(historyProvider);
    ref.invalidate(assetsProvider);
    state = AsyncData(await api.me());
  }

  Future<void> logout() async {
    await ref.read(apiProvider).clearSession();
    ref.invalidate(historyProvider);
    ref.invalidate(assetsProvider);
    state = const AsyncData(null);
  }
}

final authProvider =
    AsyncNotifierProvider<AuthNotifier, String?>(AuthNotifier.new);