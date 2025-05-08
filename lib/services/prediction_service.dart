// lib/services/prediction_service.dart

import 'dart:io';
import '../services/api_service.dart';

class PredictionService {
  /// Ensures WS is connected, sends the WAV bytes, and returns the song payload.
  static Future<Map<String, dynamic>> predict(File wavFile) async {
    final api = ApiService();
    await api.connect();
    final bytes = await wavFile.readAsBytes();
    final resp = await api.predict(bytes, format: 'wav');
    if (resp['status'] == 'ok' && resp['song'] is Map<String, dynamic>) {
      return Map<String, dynamic>.from(resp['song'] as Map);
    }
    throw Exception('Prediction failed: ${resp['reason']}');
  }

  /// Sends feedback about correctness.
  static Future<void> sendFeedback(String songName, bool correct) async {
    final api = ApiService();
    await api.connect();
    final resp = await api.sendFeedback(songName, correct);
    if (resp['status'] != 'ok') {
      throw Exception('Feedback error: ${resp['reason']}');
    }
  }
}
