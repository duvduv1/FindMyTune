// lib/pages/waiting_page.dart

import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class WaitingPage extends StatefulWidget {
  const WaitingPage({super.key});
  @override
  State<WaitingPage> createState() => _WaitingPageState();
}

class _WaitingPageState extends State<WaitingPage> {
  final ApiService _api = ApiService();
  StreamSubscription<Map<String, dynamic>>? _sub;
  bool _inited = false;

  late int _roundNumber;
  late Map<String, dynamic> _selectedRaw;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_inited) return;
    _inited = true;

    final args =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    _roundNumber = args['round_number'] as int;
    _selectedRaw = Map<String, dynamic>.from(args['selected'] as Map);

    // subscribe to your_result exactly once
    _sub = _api.messages.listen((msg) {
      final type = (msg['type'] as String?)?.toLowerCase() ?? '';
      if (type == 'your_result') {
        _sub?.cancel();
        Navigator.pushReplacementNamed(
          context,
          '/answer',
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
    final b64 = _selectedRaw['album_cover_image'] as String?;
    final Widget img = (b64 != null && b64.isNotEmpty)
        ? Image.memory(base64Decode(b64),
            width: 120, height: 120, fit: BoxFit.cover)
        : const Icon(Icons.music_note, size: 120);

    return Scaffold(
      appBar: AppBar(title: Text('Round $_roundNumber')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const Spacer(flex: 2),
            Text('Waiting for others...',
                style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 48),
            const Text('Your guess:',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            ClipRRect(borderRadius: BorderRadius.circular(8), child: img),
            const SizedBox(height: 12),
            Text(_selectedRaw['song_name'] as String,
                style:
                    const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(_selectedRaw['artist_name'] as String,
                style: const TextStyle(fontSize: 20, color: Colors.black54)),
            const Spacer(flex: 3),
          ],
        ),
      ),
    );
  }
}
