import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'config.dart';
import 'models.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient(this._storage)
      : _dio = Dio(
          BaseOptions(
            baseUrl: kApiBaseUrl,
            connectTimeout: const Duration(seconds: 15),
            sendTimeout: const Duration(seconds: 60),
            // The first upload after a server start loads both models.
            receiveTimeout: const Duration(seconds: 120),
          ),
        );

  final FlutterSecureStorage _storage;
  final Dio _dio;

  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  // ---- session ----------------------------------------------------------

  Future<bool> hasSession() async =>
      (await _storage.read(key: _refreshKey)) != null;

  Future<void> clearSession() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }

  Future<void> _saveTokens(String access, String? refresh) async {
    await _storage.write(key: _accessKey, value: access);
    if (refresh != null) {
      await _storage.write(key: _refreshKey, value: refresh);
    }
  }

  Future<void> login(String username, String password) async {
    try {
      final res = await _dio.post(
        '/auth/token/',
        data: {'username': username, 'password': password},
      );
      await _saveTokens(
        res.data['access'] as String,
        res.data['refresh'] as String?,
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw ApiException('Incorrect username or password.', statusCode: 401);
      }
      throw _toApiException(e);
    }
  }

  /// Returns true if a new access token was obtained.
  Future<bool> _refresh() async {
    final refresh = await _storage.read(key: _refreshKey);
    if (refresh == null) return false;
    try {
      final res =
          await _dio.post('/auth/token/refresh/', data: {'refresh': refresh});
      await _saveTokens(
        res.data['access'] as String,
        res.data['refresh'] as String?,
      );
      return true;
    } on DioException catch (e) {
      // Only drop the session if the server rejected the refresh token;
      // a network error should not log the inspector out.
      if (e.response?.statusCode == 401) await clearSession();
      return false;
    }
  }

  /// Runs [call] with the access token, refreshing once on a 401.
  Future<Response<dynamic>> _authed(
    Future<Response<dynamic>> Function(Options options) call,
  ) async {
    Future<Response<dynamic>> attempt() async {
      final token = await _storage.read(key: _accessKey);
      return call(Options(headers: {'Authorization': 'Bearer $token'}));
    }

    try {
      return await attempt();
    } on DioException catch (e) {
      if (e.response?.statusCode == 401 && await _refresh()) {
        try {
          return await attempt();
        } on DioException catch (e2) {
          throw _toApiException(e2);
        }
      }
      throw _toApiException(e);
    }
  }

  // ---- endpoints --------------------------------------------------------

  Future<String> me() async {
    final res = await _authed((o) => _dio.get('/auth/me/', options: o));
    return res.data['username'] as String;
  }

  Future<Inspection> uploadInspection({
    required String imagePath,
    required double latitude,
    required double longitude,
  }) async {
    final filename = imagePath.split(RegExp(r'[\\/]')).last;
    final res = await _authed((o) async {
      // FormData can only be sent once, so it is rebuilt for each attempt.
      final form = FormData.fromMap({
        'latitude': latitude,
        'longitude': longitude,
        'image': await MultipartFile.fromFile(imagePath, filename: filename),
      });
      return _dio.post('/inspect/', data: form, options: o);
    });
    return Inspection.fromJson(res.data as Map<String, dynamic>);
  }

  // ---- errors -----------------------------------------------------------

  ApiException _toApiException(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiException('The server took too long to respond. Try again.');
      case DioExceptionType.connectionError:
        return ApiException(
          'Cannot reach the server at $kApiBaseUrl. Is it running?',
        );
      default:
        break;
    }

    final code = e.response?.statusCode;
    final data = e.response?.data;
    String? detail;
    if (data is Map) {
      if (data['detail'] is String) {
        detail = data['detail'] as String;
      } else {
        detail = data.entries
            .map((en) =>
                '${en.key}: ${en.value is List ? (en.value as List).join(' ') : en.value}')
            .join('\n');
      }
    }

    switch (code) {
      case 401:
        return ApiException(
          'Sign-in failed or your session expired.',
          statusCode: 401,
        );
      case 429:
        return ApiException(
          'Too many requests. Wait a minute and try again.',
          statusCode: 429,
        );
      default:
        return ApiException(
          (detail != null && detail.isNotEmpty)
              ? detail
              : 'Request failed${code != null ? ' ($code)' : ''}.',
          statusCode: code,
        );
    }
  }
}