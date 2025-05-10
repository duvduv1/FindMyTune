// lib/pages/join_game_page.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/game_service.dart';

class JoinGamePage extends StatefulWidget {
  const JoinGamePage({super.key});

  @override
  State<JoinGamePage> createState() => _JoinGamePageState();
}

class _JoinGamePageState extends State<JoinGamePage> {
  final _formKey = GlobalKey<FormState>();
  final _idCtrl = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _idCtrl.dispose();
    super.dispose();
  }

  Future<void> _join() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    final id = _idCtrl.text.trim();
    final res = await GameService.joinGame(id);
    setState(() => _loading = false);

    if (res.success) {
      Navigator.pushReplacementNamed(
        context,
        '/lobby',
        arguments: {
          'gameId': id,
          'isHost': false,
        },
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(res.error ?? 'Join failed')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Join Game')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _idCtrl,
                decoration: const InputDecoration(labelText: 'Game ID'),
                maxLength: 8,
                inputFormatters: [
                  FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9]')),
                  LengthLimitingTextInputFormatter(8),
                ],
                validator: (v) {
                  final val = v?.trim() ?? '';
                  if (val.isEmpty) return 'Enter a game ID';
                  if (val.length != 8) return 'Game ID must be 8 characters';
                  if (!RegExp(r'^[A-Za-z0-9]{8}').hasMatch(val)) {
                    return 'Only letters and numbers allowed';
                  }
                  return null;
                },
                enabled: !_loading,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _loading ? null : _join,
                  child: _loading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2),
                        )
                      : const Text('Join'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
