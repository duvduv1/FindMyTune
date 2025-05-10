// lib/pages/signup_page.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme.dart';
import '../utils/validators.dart';
import '../services/api_service.dart';

class SignupPage extends StatefulWidget {
  const SignupPage({super.key});

  @override
  State<SignupPage> createState() => _SignupPageState();
}

class _SignupPageState extends State<SignupPage> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _loading = false;
  late final ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _apiService = ApiService();
  }

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    final uname = _usernameCtrl.text.trim();
    final pwd = _passwordCtrl.text;

    Map<String, dynamic> resp;
    try {
      await _apiService.connect();
      resp = await _apiService.signup(uname, pwd);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Error: \$e')));
      }
      resp = {'status': 'error', 'reason': e.toString()};
    } finally {
      if (mounted) setState(() => _loading = false);
    }
    if (!mounted) return;

    final success = resp['status'] == 'ok';
    if (success) {
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      final reason = resp['reason'] as String? ?? '';
      final msg = {
            'username_password_required': 'Username and password are required.',
            'user_exists': 'That username is already taken.',
            "couldn't_create_user":
                'Could not create account. Please try again.',
          }[reason] ??
          'Sign‑up failed: \$reason';

      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sign Up'),
        backgroundColor: AppTheme.primaryColor,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                // — USERNAME —
                TextFormField(
                  controller: _usernameCtrl,
                  decoration: const InputDecoration(labelText: 'Username'),
                  maxLength: 12,
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9_]')),
                    LengthLimitingTextInputFormatter(12),
                  ],
                  validator: Validators.username,
                  enabled: !_loading,
                ),
                const SizedBox(height: 16),

                // — PASSWORD —
                TextFormField(
                  controller: _passwordCtrl,
                  decoration: const InputDecoration(labelText: 'Password'),
                  obscureText: true,
                  maxLength: 12,
                  inputFormatters: [
                    LengthLimitingTextInputFormatter(12),
                  ],
                  validator: Validators.password,
                  enabled: !_loading,
                ),

                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _loading ? null : _submit,
                    child: _loading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Sign Up'),
                  ),
                ),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: _loading
                      ? null
                      : () => Navigator.pushReplacementNamed(context, '/login'),
                  child: const Text('Already have an account? Log in'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
