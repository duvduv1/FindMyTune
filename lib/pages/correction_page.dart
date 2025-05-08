// lib/pages/correction_page.dart

import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/prediction_service.dart';

class CorrectionPage extends StatelessWidget {
  const CorrectionPage({super.key});

  @override
  Widget build(BuildContext context) {
    final data =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final song = data['song_name'] as String;
    final artist = data['artist_name'] as String;
    final b64 = data['album_cover_image'] as String?;

    Uint8List? bytes;
    if (b64 != null && b64.isNotEmpty) {
      bytes = base64Decode(b64);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Was this correct?')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Found your song!',
                style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 24),
            CircleAvatar(
              radius: 60,
              backgroundColor: Colors.grey.shade200,
              backgroundImage: bytes != null ? MemoryImage(bytes) : null,
              child: bytes == null
                  ? const Icon(Icons.music_note,
                      size: 48, color: Colors.black54)
                  : null,
            ),
            const SizedBox(height: 24),
            Text(song,
                style:
                    const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(artist,
                style: const TextStyle(fontSize: 18, color: Colors.black54)),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  icon: const Icon(Icons.thumb_up),
                  label: const Text('Yes'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryColor,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 24, vertical: 12),
                  ),
                  onPressed: () async {
                    await PredictionService.sendFeedback(song, true);
                    Navigator.pushNamedAndRemoveUntil(
                        context, '/home', (r) => false);
                  },
                ),
                ElevatedButton.icon(
                  icon: const Icon(Icons.thumb_down),
                  label: const Text('No'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryColor,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 24, vertical: 12),
                  ),
                  onPressed: () async {
                    await PredictionService.sendFeedback(song, false);
                    Navigator.pushNamedAndRemoveUntil(
                        context, '/home', (r) => false);
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
