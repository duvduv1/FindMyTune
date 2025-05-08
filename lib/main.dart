import 'dart:io';

import 'package:flutter/material.dart';
import 'theme.dart';
import 'pages/login_page.dart';
import 'pages/signup_page.dart';
import 'pages/home_page.dart';
import 'pages/game_hub_page.dart';
import 'pages/join_game_page.dart';
import 'pages/lobby_page.dart';
import 'pages/round_page.dart';
import 'pages/waiting_page.dart';
import 'pages/answer_page.dart';
import 'pages/round_results_page.dart';
import 'pages/final_results_page.dart';
import 'pages/song_page.dart';
import 'pages/prediction_page.dart';
import 'pages/correction_page.dart';

/// Allows self-signed or invalid SSL certificates (development only).
class _AllowBadCerts extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      // Accept any certificate (not secure for production!)
      ..badCertificateCallback = (cert, host, port) => true;
  }
}

void main() {
  HttpOverrides.global = _AllowBadCerts();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MusicGuess',
      theme: AppTheme.theme,
      initialRoute: '/login',
      routes: {
        '/login': (ctx) => const LoginPage(),
        '/signup': (ctx) => const SignupPage(),
        '/home': (ctx) => const HomePage(),
        '/game_hub': (ctx) => const GameHubPage(),
        '/join_game': (ctx) => const JoinGamePage(),
        '/lobby': (ctx) => const LobbyPage(),
        '/round': (ctx) => const RoundPage(),
        '/waiting': (ctx) => const WaitingPage(),
        '/answer': (ctx) => const AnswerPage(),
        '/round_results': (ctx) => const RoundResultsPage(),
        '/final_results': (ctx) => const FinalResultsPage(),
        '/song': (ctx) => const SongPage(),
        '/prediction': (ctx) => const PredictionPage(),
        '/correction': (ctx) => const CorrectionPage(),
      },
      debugShowCheckedModeBanner: false,
    );
  }
}
