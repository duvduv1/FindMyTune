// lib/utils/storage.dart

import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const _keyToken = 'session_token';

  /// Persist the session token.
  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyToken, token);
  }

  /// Read back the token (or null if none).
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyToken);
  }

  /// Remove the stored token on logout.
  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyToken);
  }
}
