// lib/pages/prediction_page.dart

import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';

import '../theme.dart';
import '../services/prediction_service.dart';

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});
  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage>
    with SingleTickerProviderStateMixin {
  final AudioRecorder _recorder = AudioRecorder();
  late AnimationController _pulseController;
  late Animation<double> _pulse;
  bool _recording = false;
  File? _wavFile;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    );
    _pulse = Tween(begin: 1.0, end: 1.1).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  Future<void> _startRecording() async {
    // 1) Check and request permission
    if (!await _recorder.hasPermission()) {
      final granted = await _recorder.hasPermission();
      if (!granted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Microphone permission denied')),
        );
        return;
      }
    }

    final dir = await getTemporaryDirectory();
    final path = '${dir.path}/clip.wav';
    await _recorder.start(
      const RecordConfig(
          encoder: AudioEncoder.wav, bitRate: 128000, sampleRate: 22050),
      path: path,
    );

    setState(() => _recording = true);
    _pulseController.repeat(reverse: true);
    Future.delayed(const Duration(seconds: 5), _stopRecording);
  }

  Future<void> _stopRecording() async {
    final path = await _recorder.stop();
    setState(() {
      _recording = false;
      if (path != null) _wavFile = File(path);
    });
    _pulseController.stop();
    _pulseController.reset();
    _submitForPrediction();
  }

  Future<void> _submitForPrediction() async {
    if (_wavFile == null) return;
    setState(() => _loading = true);
    try {
      final song = await PredictionService.predict(_wavFile!);
      Navigator.pushReplacementNamed(context, '/correction', arguments: song);
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Error: $e')));
      setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _recorder.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.primaryColor;
    return Scaffold(
      appBar: AppBar(title: const Text('Predict Song')),
      body: Center(
        child: _loading
            ? const CircularProgressIndicator()
            : GestureDetector(
                onTap: _recording ? null : _startRecording,
                child: ScaleTransition(
                  scale: _pulse,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    width: _recording ? 180 : 140,
                    height: _recording ? 180 : 140,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: color.withOpacity(0.1),
                    ),
                    child: Center(
                      child: Image.asset(
                        'assets/logo.png', // match HomePage logo
                        width: 200,
                        height: 200,
                      ),
                    ),
                  ),
                ),
              ),
      ),
    );
  }
}
