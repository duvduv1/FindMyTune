import 'dart:convert';
import 'package:crypto/crypto.dart';

class HashUtils {
  static String hashPassword(String pwd) {
    // Simple SHA‑256; server must accept this
    final bytes = utf8.encode(pwd);
    return sha256.convert(bytes).toString();
  }
}
