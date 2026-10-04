import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_client.dart';

final storageProvider = Provider<FlutterSecureStorage>(
  (ref) => const FlutterSecureStorage(),
);

final apiProvider = Provider<ApiClient>(
  (ref) => ApiClient(ref.watch(storageProvider)),
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
    state = AsyncData(await api.me());
  }

  Future<void> logout() async {
    await ref.read(apiProvider).clearSession();
    state = const AsyncData(null);
  }
}

final authProvider =
    AsyncNotifierProvider<AuthNotifier, String?>(AuthNotifier.new);