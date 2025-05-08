// lib/pages/round_page.dart

import 'dart:async';
import 'dart:io';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:audioplayers/audioplayers.dart';

import '../services/api_service.dart';

class RoundPage extends StatefulWidget {
  const RoundPage({super.key});

  @override
  State<RoundPage> createState() => _RoundPageState();
}

class _RoundPageState extends State<RoundPage> {
  bool _inited = false;
  late int _roundNumber;
  late int _roundTime;
  late String _clipBase64;
  String? _clipFilePath;

  late final List<Map<String, dynamic>> _rawOptions;
  late final List<_SongOption> _songOptions;
  final AudioPlayer _audioPlayer = AudioPlayer();
  final ValueNotifier<int> _remaining = ValueNotifier(0);
  Timer? _timer;
  final ApiService _api = ApiService();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_inited) return;
    _inited = true;

    final args =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    _roundNumber = args['round_number'] as int;
    _roundTime = args['round_time'] as int;
    _clipBase64 = args['clip_b64'] as String;
    _rawOptions = List<Map<String, dynamic>>.from(args['options'] as List);

    // Decode options into typed list with cached images
    _songOptions = _rawOptions.map((opt) {
      final b64 = opt['album_cover_image'] as String?;
      ImageProvider img;
      if (b64 != null && b64.isNotEmpty) {
        img = MemoryImage(base64Decode(b64));
      } else {
        img = const AssetImage('assets/default_album.png');
      }
      return _SongOption(
        songName: opt['song_name'] as String,
        artistName: opt['artist_name'] as String,
        albumArt: img,
      );
    }).toList();

    // Prepare and play the clip
    _prepareClip(_clipBase64).then((path) {
      _clipFilePath = path;
      _playClip();
    });

    // Start countdown
    _startTimer();
  }

  Future<String> _prepareClip(String b64) async {
    final bytes = base64Decode(b64);
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/round_$_roundNumber.mp3');
    await file.writeAsBytes(bytes, flush: true);
    return file.path;
  }

  Future<void> _playClip() async {
    if (_clipFilePath == null) return;
    try {
      await _audioPlayer.play(DeviceFileSource(_clipFilePath!));
    } catch (_) {}
  }

  void _startTimer() {
    _remaining.value = _roundTime;
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      final rem = _remaining.value - 1;
      if (rem <= 0) {
        t.cancel();
        _remaining.value = 0;
      } else {
        _remaining.value = rem;
      }
    });
  }

  Future<void> _submitGuess(int index) async {
    final opt = _rawOptions[index];
    final elapsed = _roundTime - _remaining.value;
    await _api.send({
      'action': 'guess',
      'data': {
        'token': _api.token,
        'guess': opt['song_name'],
        'guess_time': elapsed,
      },
    });

    Navigator.pushReplacementNamed(
      context,
      '/waiting',
      arguments: {
        'round_number': _roundNumber,
        'selected': opt,
      },
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _audioPlayer.dispose();
    _remaining.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_inited) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(title: Text('Round $_roundNumber')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            ValueListenableBuilder<int>(
              valueListenable: _remaining,
              builder: (_, rem, __) => Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Time left: $rem s',
                      style: Theme.of(context).textTheme.headlineSmall),
                  IconButton(
                      icon: const Icon(Icons.volume_up), onPressed: _playClip),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Expanded(
              child: GridView.builder(
                itemCount: _songOptions.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 1,
                  childAspectRatio: 1.2,
                  mainAxisSpacing: 16,
                ),
                itemBuilder: (ctx, i) {
                  final opt = _songOptions[i];
                  return InkWell(
                    onTap: () => _submitGuess(i),
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey.shade400),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        children: [
                          Expanded(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: Image(
                                  image: opt.albumArt,
                                  fit: BoxFit.cover,
                                  width: double.infinity),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Text(opt.songName,
                              style: const TextStyle(
                                  fontSize: 20, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          Text(opt.artistName,
                              style: const TextStyle(
                                  fontSize: 18, color: Colors.black54)),
                        ],
                      ),
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
}

class _SongOption {
  final String songName;
  final String artistName;
  final ImageProvider albumArt;
  _SongOption({
    required this.songName,
    required this.artistName,
    required this.albumArt,
  });
}
