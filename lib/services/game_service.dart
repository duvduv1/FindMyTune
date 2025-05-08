// lib/services/game_service.dart

import 'dart:async';
import 'api_service.dart';

class CreateGameResult {
  final bool success;
  final String? gameId;
  final String? error;
  CreateGameResult({required this.success, this.gameId, this.error});
}

class JoinGameResult {
  final bool success;
  final String? error;
  JoinGameResult({required this.success, this.error});
}

class GameService {
  // Reuse your singleton ApiService
  static final ApiService _api = ApiService();

  /// Connects (if needed) and sends the create_game request.
  static Future<CreateGameResult> createGame() async {
    try {
      await _api.connect();
      final resp = await _api.createGame(); // calls ApiService.createGame()
      print('[GameService] createGame response → $resp');
      if (resp['status'] == 'ok' && resp['game_id'] is String) {
        return CreateGameResult(
          success: true,
          gameId: resp['game_id'] as String,
        );
      } else {
        return CreateGameResult(
          success: false,
          error: resp['reason'] as String? ?? 'Failed to create game',
        );
      }
    } catch (e, st) {
      print('[GameService] createGame error → $e\n$st');
      return CreateGameResult(success: false, error: e.toString());
    }
  }

  /// Connects (if needed) and sends the join_game request.
  static Future<JoinGameResult> joinGame(String gameId) async {
    try {
      await _api.connect();
      final resp = await _api.joinGame(gameId); // calls ApiService.joinGame()
      print('[GameService] joinGame response → $resp');
      if (resp['status'] == 'ok') {
        return JoinGameResult(success: true, error: null);
      } else {
        return JoinGameResult(
          success: false,
          error: resp['reason'] as String? ?? 'Failed to join game',
        );
      }
    } catch (e, st) {
      print('[GameService] joinGame error → $e\n$st');
      return JoinGameResult(success: false, error: e.toString());
    }
  }
}
