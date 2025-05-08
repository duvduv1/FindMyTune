// lib/pages/lobby_page.dart

import 'dart:async';
import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api_service.dart';

class LobbyPage extends StatefulWidget {
  const LobbyPage({super.key});

  @override
  State<LobbyPage> createState() => _LobbyPageState();
}

class _LobbyPageState extends State<LobbyPage> {
  String? _gameId;
  final ApiService _api = ApiService();

  StreamSubscription<Map<String, dynamic>>? _sub;
  List<Map<String, dynamic>> _players = [];
  Map<String, int> _settings = {'num_rounds': 10, 'round_time': 30};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final args =
          ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
      _gameId = args['gameId'] as String;
      final isHost = args['isHost'] as bool;

      // Only join if you’re a joiner
      if (!isHost) {
        //_api.joinLobby(_gameId!);
      }

      // In either case, start listening once
      _sub = _api.messages.listen(_onMessage);
      _api.getLobbyPlayers().then((players) {
        if (mounted) setState(() => _players = players);
      });
      setState(() {}); // fire a rebuild so build() sees non-null _gameId
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  void _onMessage(Map<String, dynamic> msg) {
    final action = (msg['action'] as String?)?.toLowerCase() ??
        (msg['type'] as String?)?.toLowerCase() ??
        '';
    final data = msg['data'] as Map<String, dynamic>? ?? {};

    switch (action) {
      // Initial full state
      case 'game_state':
        final s = data['settings'] as Map<String, dynamic>;
        final list = List<Map<String, dynamic>>.from(data['players'] as List);
        setState(() {
          _settings = {
            'num_rounds': s['num_rounds'] as int,
            'round_time': s['round_time'] as int,
          };
          _players = list;
        });
        break;

      // Add one
      case 'player_joined':
        final newPlayer = {
          'id': data['player_id'],
          'username': data['username'],
        };
        setState(() {
          // avoid dupes
          _players.removeWhere((p) => p['id'] == newPlayer['id']);
          _players.add(newPlayer);
        });
        break;

      // Remove one
      case 'player_left':
        final leftId = data['player_id'];
        setState(() {
          _players.removeWhere((p) => p['id'] == leftId);
        });
        break;

      // Settings change
      case 'settings_updated':
        final s = data['settings'] as Map<String, dynamic>;
        setState(() {
          _settings = {
            'num_rounds': s['num_rounds'] as int,
            'round_time': s['round_time'] as int,
          };
        });
        break;

      // Round start
      case 'round_start':
        Navigator.pushReplacementNamed(context, '/round', arguments: data);
        break;

      // Kicked out
      case 'kicked':
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('You were removed from the lobby')),
        );
        Navigator.pushReplacementNamed(context, '/game_hub');
        break;
    }
  }

  Future<void> _updateSetting(String key) async {
    final current = _settings[key]!;
    final ctrl = TextEditingController(text: '$current');
    final result = await showDialog<int?>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Set ${key.replaceAll('_', ' ')}'),
        content: TextField(
          controller: ctrl,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(hintText: '$current'),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(context, int.tryParse(ctrl.text)),
              child: const Text('OK')),
        ],
      ),
    );

    if (result != null) {
      if (key == 'num_rounds') {
        await _api.updateLobbySettings(numRounds: result);
      } else {
        await _api.updateLobbySettings(roundTime: result);
      }
    }
  }

  void _startGame() {
    _api.startGame();
  }

  void _kickPlayer(String username) {
    if (_gameId != null) {
      _api.kickPlayer(_gameId!, username);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_gameId == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(backgroundColor: AppTheme.primaryColor),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Game ID: $_gameId',
                style:
                    const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              _buildSettingCircle('Rounds', 'num_rounds'),
              const SizedBox(width: 16),
              _buildSettingCircle('Time', 'round_time'),
              const SizedBox(width: 32),
              ElevatedButton(
                onPressed: _startGame,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
                child: const Text('Start Game', style: TextStyle(fontSize: 18)),
              ),
            ]),
            const SizedBox(height: 24),
            const Text('Players:',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: _players.length,
                itemBuilder: (ctx, i) {
                  final p = _players[i];
                  final username = p['username'] as String;
                  final isSelf = username == _api.username;
                  return ListTile(
                    title: Text(username, style: const TextStyle(fontSize: 16)),
                    tileColor: isSelf ? AppTheme.primaryLightColor : null,
                    trailing: isSelf
                        ? null
                        : IconButton(
                            icon: const Icon(Icons.person_remove,
                                color: Colors.red),
                            onPressed: () => _kickPlayer(username),
                          ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingCircle(String label, String key) {
    return GestureDetector(
      onTap: () => _updateSetting(key),
      child: Column(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: AppTheme.primaryColor.withOpacity(0.2),
            child:
                Text('${_settings[key]}', style: const TextStyle(fontSize: 20)),
          ),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 14)),
        ],
      ),
    );
  }
}
