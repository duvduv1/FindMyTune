// lib/pages/round_results_page.dart

import 'dart:async';
import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api_service.dart';

class RoundResultsPage extends StatefulWidget {
  const RoundResultsPage({super.key});

  @override
  State<RoundResultsPage> createState() => _RoundResultsPageState();
}

class _RoundResultsPageState extends State<RoundResultsPage> {
  final ApiService _api = ApiService();
  StreamSubscription<Map<String, dynamic>>? _sub;
  bool _inited = false;

  late List<Map<String, dynamic>> _placements;
  late bool _waitingForHost;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_inited) return;
    _inited = true;

    final data =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    _placements =
        List<Map<String, dynamic>>.from(data['placements_table'] as List);
    _waitingForHost = data['waiting_for_host'] as bool;

    // Listen once for 'round_start' → push to RoundPage
    _sub = _api.messages.listen((msg) {
      final type = (msg['type'] as String?)?.toLowerCase() ?? '';
      if (type == 'round_start') {
        _sub?.cancel();
        Navigator.pushReplacementNamed(
          context,
          '/round',
          arguments: msg['data'] as Map<String, dynamic>,
        );
      } else if (type == 'game_ended') {
        _sub?.cancel();
        Navigator.pushReplacementNamed(
          context,
          '/final_results',
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

  void _onNextRound() {
    _api.send({
      'action': 'next_round',
      'data': {'token': _api.token},
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Round Results')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                // allow horizontal scrolling
                scrollDirection: Axis.horizontal,
                child: ConstrainedBox(
                  // make the table at least as wide as the screen
                  constraints: BoxConstraints(
                    minWidth: MediaQuery.of(context).size.width - 48,
                  ),
                  child: SingleChildScrollView(
                    // now vertical scroll for rows
                    child: DataTable(
                      headingRowHeight: 56,
                      dataRowHeight: 56,
                      dividerThickness: 1,
                      columnSpacing: 24,
                      columns: const [
                        DataColumn(
                          label: Text('Place',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                        DataColumn(
                          label: Text('User',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                        DataColumn(
                          numeric: true,
                          label: Text('Round',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                        DataColumn(
                          numeric: true,
                          label: Text('score',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                      ],
                      rows: _placements.map((p) {
                        return DataRow(cells: [
                          DataCell(Text('${p['placement']}',
                              style: const TextStyle(fontSize: 16))),
                          DataCell(Text(p['username'] as String,
                              style: const TextStyle(fontSize: 16))),
                          DataCell(Text('+${p['points_this_round']}',
                              style: const TextStyle(fontSize: 16))),
                          DataCell(Text('${p['total_score']}',
                              style: const TextStyle(fontSize: 16))),
                        ]);
                      }).toList(),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            if (_waitingForHost)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _onNextRound,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryColor,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text(
                    'Next Round',
                    style: TextStyle(fontSize: 18, color: Colors.white),
                  ),
                ),
              )
            else
              const Text(
                'Waiting for host to start next round...',
                style: TextStyle(fontSize: 16, fontStyle: FontStyle.italic),
              ),
          ],
        ),
      ),
    );
  }
}
