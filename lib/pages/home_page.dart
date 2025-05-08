// lib/pages/home_page.dart

import 'dart:convert';
import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api_service.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // Service
  late final ApiService _apiService;
  late Future<List<Map<String, dynamic>>> _historyFuture;

  // Layout control constants
  final double gameButtonWidth = 280;
  final double gameButtonHeight = 80;
  final double predictButtonDiameter = 370; // set your desired size
  final double verticalSpacing = 16;
  final double historyListHeight = 350;

  @override
  void initState() {
    super.initState();
    _apiService = ApiService();
    _historyFuture = _loadHistory();
  }

  Future<List<Map<String, dynamic>>> _loadHistory() async {
    try {
      await _apiService.connect();
      final resp = await _apiService.getHistory();
      if (resp['status'] == 'ok' && resp['history'] is List) {
        return List<Map<String, dynamic>>.from(resp['history']);
      }
    } catch (_) {
      // ignore errors
    }
    return [];
  }

  @override
  Widget build(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;

    return Scaffold(
      body: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Notch-level bar + extension
              Container(
                height: topPadding + 4,
                color: AppTheme.primaryColor,
              ),

              // Logout button
              Padding(
                padding: const EdgeInsets.only(top: 8, left: 16),
                child: Align(
                  alignment: Alignment.topLeft,
                  child: InkWell(
                    onTap: () async {
                      await _apiService.logout();
                      Navigator.pushReplacementNamed(context, '/login');
                    },
                    borderRadius: BorderRadius.circular(20),
                    child: Ink(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppTheme.primaryColor,
                          width: 2,
                        ),
                      ),
                      child: const Icon(
                        Icons.logout,
                        color: AppTheme.primaryColor,
                        size: 20,
                      ),
                    ),
                  ),
                ),
              ),

              // Spacer
              SizedBox(height: verticalSpacing),

              // Game button
              Center(
                child: SizedBox(
                  width: gameButtonWidth,
                  height: gameButtonHeight,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      side: const BorderSide(color: Colors.black, width: 2),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 0,
                    ),
                    onPressed: () {
                      Navigator.pushNamed(context, '/game_hub');
                    },
                    child: const Text(
                      'Play Game',
                      style: TextStyle(
                        fontFamily: 'Honk',
                        fontSize: 45,
                        color: Colors.black,
                      ),
                    ),
                  ),
                ),
              ),

              // Spacer
              SizedBox(height: verticalSpacing),

              // Predict button (fixed size)
              Center(
                child: GestureDetector(
                  onTap: () => Navigator.pushNamed(context, '/prediction'),
                  child: Container(
                    width: predictButtonDiameter,
                    height: predictButtonDiameter,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppTheme.primaryColor.withOpacity(0.1),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Image.asset('assets/logo.png'),
                    ),
                  ),
                ),
              ),

              // Spacer
              SizedBox(height: verticalSpacing),

              // Search history heading
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
                child: const Text(
                  'Your Search History',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),

              // History list
              SizedBox(
                height: historyListHeight,
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _historyFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    final history = snapshot.data;
                    if (history == null || history.isEmpty) {
                      return const Center(child: Text('No history yet.'));
                    }
                    return ListView.builder(
                      padding: const EdgeInsets.only(bottom: 16),
                      itemCount: history.length,
                      itemBuilder: (context, i) {
                        final item = history[i];
                        final b64 = item['album_cover_image'] as String?;
                        final imageBytes = (b64 != null && b64.isNotEmpty)
                            ? base64Decode(b64)
                            : null;

                        Widget avatar = (imageBytes != null)
                            ? Container(
                                width: 72,
                                height: 72,
                                decoration: BoxDecoration(
                                  image: DecorationImage(
                                    image: MemoryImage(imageBytes),
                                    fit: BoxFit.cover,
                                  ),
                                  borderRadius: BorderRadius.circular(4),
                                  border:
                                      Border.all(color: Colors.grey.shade300),
                                ),
                              )
                            : Container(
                                width: 72,
                                height: 72,
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade200,
                                  borderRadius: BorderRadius.circular(4),
                                  border:
                                      Border.all(color: Colors.grey.shade300),
                                ),
                                child: const Icon(Icons.music_note,
                                    size: 28, color: Colors.black54),
                              );

                        // Wrap the tile in InkWell:
                        return InkWell(
                          onTap: () {
                            Navigator.pushNamed(
                              context,
                              '/song',
                              arguments: item, // pass the song data map
                            );
                          },
                          child: Container(
                            margin: const EdgeInsets.symmetric(
                                horizontal: 16, vertical: 8),
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              border: Border.all(color: Colors.grey.shade300),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Row(
                              children: [
                                avatar,
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        item['song_name'] as String,
                                        style: const TextStyle(
                                          fontSize: 22,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        item['artist_name'] as String,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          color: Colors.black54,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
