// lib/pages/song_page.dart

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme.dart';
import '../services/api_service.dart';

class SongPage extends StatefulWidget {
  const SongPage({Key? key}) : super(key: key);

  @override
  State<SongPage> createState() => _SongPageState();
}

class _SongPageState extends State<SongPage> {
  late final Map<String, dynamic> _initialSong;
  late final Future<List<Map<String, dynamic>>> _historyFuture;
  late final PageController _pageController;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _initialSong =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    _historyFuture = _loadHistory();
  }

  Future<List<Map<String, dynamic>>> _loadHistory() async {
    final resp = await ApiService().getHistory();
    final list = List<Map<String, dynamic>>.from(resp['history'] ?? []);
    int idx = list.indexWhere((item) =>
        item['song_name'] == _initialSong['song_name'] &&
        item['artist_name'] == _initialSong['artist_name'] &&
        item['played_at'] == _initialSong['played_at']);
    if (idx < 0) idx = 0;
    _pageController = PageController(initialPage: idx);
    return list;
  }

  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open URL')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(backgroundColor: AppTheme.primaryColor),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _historyFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final history = snapshot.data ?? [];
          if (history.isEmpty) {
            return const Center(child: Text('No history available.'));
          }

          return PageView.builder(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            itemCount: history.length,
            itemBuilder: (context, index) {
              final song = history[index];
              final b64 = song['album_cover_image'] as String?;
              Widget cover = Container(
                width: 240,
                height: 240,
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: (b64 != null && b64.isNotEmpty)
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.memory(
                          base64Decode(b64),
                          fit: BoxFit.cover,
                        ),
                      )
                    : const Center(
                        child: Icon(
                          Icons.music_note,
                          size: 64,
                          color: Colors.grey,
                        ),
                      ),
              );

              // Fields
              final title = song['song_name'] as String? ?? 'Unknown Title';
              final artist = song['artist_name'] as String? ?? 'Unknown Artist';

              // Album or Single
              final type = (song['album_type'] as String? ?? '').toLowerCase();
              final albumName = song['album_name'] as String?;
              final albumText = type == 'single'
                  ? 'Single'
                  : (albumName != null && albumName.isNotEmpty)
                      ? 'Album: $albumName'
                      : '';

              // Prediction date
              final playedAt = song['played_at'] as String? ?? '';

              // Release date
              final releaseDate = song['release_date'] as String?;

              final spotifyUrl = song['spotify_url'] as String?;

              return SingleChildScrollView(
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(vertical: 50, horizontal: 16),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      cover,
                      const SizedBox(height: 24),
                      Text(
                        title,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        artist,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 24,
                          color: Colors.black54,
                        ),
                      ),
                      if (albumText.isNotEmpty) ...[
                        const SizedBox(height: 16),
                        Text(
                          albumText,
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 20),
                        ),
                      ],
                      // Release Date
                      if (releaseDate != null && releaseDate.isNotEmpty) ...[
                        const SizedBox(height: 16),
                        Text(
                          'Release date: $releaseDate',
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 18),
                        ),
                      ],
                      const SizedBox(height: 16),
                      Text(
                        'Prediction date: $playedAt',
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 18),
                      ),
                      if (spotifyUrl != null && spotifyUrl.isNotEmpty) ...[
                        const SizedBox(height: 24),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.primaryColor,
                          ),
                          onPressed: () => _launchUrl(spotifyUrl),
                          child: const Text('Open on Spotify'),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
