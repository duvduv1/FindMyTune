// lib/pages/game_hub_page.dart

import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/game_service.dart';

class GameHubPage extends StatelessWidget {
  const GameHubPage({super.key});

  @override
  Widget build(BuildContext context) {
    // Layout constants
    const double buttonWidth = 280;
    const double buttonHeight = 60;
    const double verticalSpacing = 24;

    return Scaffold(
      appBar: AppBar(backgroundColor: AppTheme.primaryColor),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Drop down a bit
              const SizedBox(height: 100),

              // Page title
              Center(
                child: Text(
                  'Game Hub',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
              ),

              // Additional spacing before buttons
              const SizedBox(height: 48),

              // Create Game button
              Center(
                child: SizedBox(
                  width: buttonWidth,
                  height: buttonHeight,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryColor,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed: () async {
                      final res = await GameService.createGame();
                      if (res.success && res.gameId != null) {
                        Navigator.pushReplacementNamed(
                          context,
                          '/lobby',
                          arguments: {
                            'gameId': res.gameId!,
                            'isHost': true,
                          },
                        );
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(res.error ?? 'Create failed')),
                        );
                      }
                    },
                    child: const Text(
                      'Create Game',
                      style: TextStyle(
                        fontSize: 18,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ),

              // Space between buttons
              const SizedBox(height: verticalSpacing),

              // Join Game button
              Center(
                child: SizedBox(
                  width: buttonWidth,
                  height: buttonHeight,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      side: const BorderSide(
                          color: AppTheme.primaryColor, width: 2),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 0,
                    ),
                    onPressed: () {
                      Navigator.pushNamed(context, '/join_game');
                    },
                    child: Text(
                      'Join Game',
                      style: TextStyle(
                        fontSize: 18,
                        color: AppTheme.primaryColor,
                      ),
                    ),
                  ),
                ),
              ),

              // Push content up if room
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }
}
