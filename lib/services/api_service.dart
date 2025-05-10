// lib/services/api_service.dart

import 'dart:async';
import 'dart:convert';
import 'package:music_guess/utils/storage.dart';

import '../utils/ws_constants.dart';
import 'secure_ws.dart';

/// Central API service wrapping a single SecureWS connection.
class ApiService {
  // Singleton
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal() : _ws = SecureWS(serverURL);

  final SecureWS _ws;
  String? _token;
  String? _username;

  /// Ensure WebSocket is open
  Future<void> connect() async {
    try {
      await _ws.connect();
    } catch (_) {
      // already connected
    }
  }

  /// Raw incoming JSON messages
  Stream<Map<String, dynamic>> get messages => _ws.messages;

  /// Send any JSON payload
  Future<void> send(Map<String, dynamic> message) => _ws.send(message);

  /// Current session token
  String? get token => _token;

  /// Logged-in username
  String? get username => _username;

  // -------------------- Authentication -------------------- //

  Future<Map<String, dynamic>> signup(String username, String password) async {
    await connect();
    await send({
      'action': 'signup',
      'data': {'username': username, 'password': password},
    });
    final resp = await messages.firstWhere((m) => m.containsKey('status'));
    if (resp['status'] == 'ok' && resp.containsKey('token')) {
      _token = resp['token'] as String;
      _username = username;
      // persist
      await StorageService.saveToken(_token!);
    }
    return resp;
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    await connect();
    await send({
      'action': 'login',
      'data': {'username': username, 'password': password},
    });
    final resp = await messages.firstWhere((m) => m.containsKey('status'));
    if (resp['status'] == 'ok' && resp.containsKey('token')) {
      _token = resp['token'] as String;
      _username = username;
      // persist
      await StorageService.saveToken(_token!);
    }
    return resp;
  }

  /// Logs out remotely and clears all local state.
  Future<void> logout() async {
    if (_token != null) {
      await send({
        'action': 'logout',
        'data': {'token': _token},
      });
      await messages.firstWhere((m) => m.containsKey('status'));
    }
    // tear down WS & token
    await _ws.close();
    await StorageService.clearToken();
    _token = null;
    _username = null;
  }

  // -------------------- History -------------------- //

  Future<Map<String, dynamic>> getHistory() async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'get_history',
      'data': {'token': _token}
    });
    return await messages.firstWhere((m) => m.containsKey('status'));
  }

  // -------------------- Prediction -------------------- //

  Future<Map<String, dynamic>> predict(List<int> audioBytes,
      {String format = 'wav'}) async {
    if (_token == null) throw Exception('Not authenticated');
    final audioB64 = base64Encode(audioBytes);
    await send({
      'action': 'predict',
      'data': {'token': _token, 'audio': audioB64, 'format': format},
    });
    return await messages.firstWhere((m) => m.containsKey('status'));
  }

  Future<Map<String, dynamic>> sendFeedback(
      String songName, bool correct) async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'prediction_feedback',
      'data': {'token': _token, 'song_name': songName, 'correct': correct},
    });
    return await messages.firstWhere((m) => m.containsKey('status'));
  }

  // -------------------- Game -------------------- //

  Future<Map<String, dynamic>> createGame() async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'create_game',
      'data': {'token': _token}
    });
    return await messages.firstWhere((m) => m.containsKey('status'));
  }

  Future<Map<String, dynamic>> joinGame(String gameId) async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'join_game',
      'data': {'token': _token, 'game_id': gameId},
    });
    return await messages.firstWhere((m) => m.containsKey('status'));
  }

  Future<Map<String, dynamic>> guess(String playerId, String guess) async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'guess',
      'data': {'token': _token, 'player_id': playerId, 'guess': guess},
    });
    return await messages.firstWhere((m) => m.containsKey('status'));
  }

  // -------------------- Lobby Helpers -------------------- //

  /// Join a lobby (will receive initial `game_state`)
  Future<void> joinLobby(String gameId) async {
    if (_token == null) throw Exception('Not authenticated');
    await connect();
    await send({
      'action': 'join_game',
      'data': {'token': _token, 'game_id': gameId},
    });
  }

  /// Fetch the current lobby’s players list.
  Future<List<Map<String, dynamic>>> getLobbyPlayers() async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'get_players',
      'data': {'token': _token},
    });
    final msg = await messages.firstWhere((m) => m['type'] == 'players');
    final data = msg['data'] as Map<String, dynamic>;
    return List<Map<String, dynamic>>.from(data['players'] as List);
  }

  /// Update number of rounds and/or round duration
  Future<void> updateLobbySettings({int? numRounds, int? roundTime}) async {
    if (_token == null) throw Exception('Not authenticated');

    // Explicitly type as dynamic so we can mix Strings and ints
    final Map<String, dynamic> data = {'token': _token};

    if (numRounds != null) data['num_rounds'] = numRounds;
    if (roundTime != null) data['round_time'] = roundTime;

    await send({'action': 'update_settings', 'data': data});
  }

  /// Tell the server to begin the game
  Future<void> startGame() async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'start_game',
      'data': {'token': _token},
    });
  }

  /// Kick a player by username (host only)
  Future<void> kickPlayer(String gameId, String username) async {
    if (_token == null) throw Exception('Not authenticated');
    await send({
      'action': 'kick_player',
      'data': {'token': _token, 'game_id': gameId, 'username': username},
    });
  }
}
