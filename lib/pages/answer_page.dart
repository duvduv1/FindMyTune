// lib/pages/answer_page.dart

import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AnswerPage extends StatefulWidget {
  const AnswerPage({super.key});
  @override
  State<AnswerPage> createState() => _AnswerPageState();
}

class _AnswerPageState extends State<AnswerPage> {
  final ApiService _api = ApiService();
  StreamSubscription<Map<String, dynamic>>? _sub;
  bool _inited = false;

  late bool _correct;
  late int _pointsEarned;
  late int _totalScore;
  late Map<String, dynamic> _correctSong;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_inited) return;
    _inited = true;

    final data =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    _correct = data['correct'] as bool;
    _pointsEarned = data['points_earned'] as int;
    _totalScore = data['total_score'] as int;
    _correctSong = Map<String, dynamic>.from(data['correct_answer'] as Map);

    // subscribe to round_end exactly once
    _sub = _api.messages.listen((msg) {
      final type = (msg['type'] as String?)?.toLowerCase() ?? '';
      if (type == 'round_end') {
        _sub?.cancel();
        Navigator.pushReplacementNamed(
          context,
          '/round_results',
          arguments: msg['data'] as Map<String, dynamic>,
        );
      }
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final b64 = _correctSong['album_cover_image'] as String?;
    final Widget img = (b64 != null && b64.isNotEmpty)
        ? Image.memory(base64Decode(b64),
            width: 140, height: 140, fit: BoxFit.cover)
        : const Icon(Icons.music_note, size: 140);

    return Scaffold(
      appBar: AppBar(title: const Text('Answer')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Text(
              _correct ? 'Correct!' : 'Wrong!',
              style: Theme.of(context)
                  .textTheme
                  .headlineLarge!
                  .copyWith(color: _correct ? Colors.green : Colors.red),
            ),
            if (!_correct) ...[
              const SizedBox(height: 12),
              const Text('Correct answer:',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ],
            const SizedBox(height: 24),
            ClipRRect(borderRadius: BorderRadius.circular(8), child: img),
            const SizedBox(height: 16),
            Text(_correctSong['song_name'] as String,
                style:
                    const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(_correctSong['artist_name'] as String,
                style: const TextStyle(fontSize: 18, color: Colors.black54)),
            const SizedBox(height: 32),
            if (_correct) ...[
              Text('Points earned: $_pointsEarned',
                  style: const TextStyle(fontSize: 18)),
              const SizedBox(height: 8),
            ],
            Text('Total score: $_totalScore',
                style: const TextStyle(fontSize: 18)),
            const Spacer(),
            const Text(
              'Waiting for next round...',
              style: TextStyle(fontSize: 16, fontStyle: FontStyle.italic),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
