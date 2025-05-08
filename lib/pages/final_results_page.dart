// lib/pages/final_results_page.dart

import 'package:flutter/material.dart';
import '../theme.dart';

class FinalResultsPage extends StatelessWidget {
  const FinalResultsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final args =
        ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
    final rankings = List<Map<String, dynamic>>.from(args['rankings'] as List);
    final winner = args['winner'] as Map<String, dynamic>?;

    return Scaffold(
      appBar: AppBar(title: const Text('Game Over')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Game Ended!',
              style: Theme.of(context).textTheme.headlineLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            if (winner != null) ...[
              Text(
                'Winner: ${winner['username']}',
                style: Theme.of(context)
                    .textTheme
                    .headlineMedium!
                    .copyWith(color: AppTheme.primaryColor),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
            ],
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                      minWidth: MediaQuery.of(context).size.width - 48),
                  child: SingleChildScrollView(
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
                          label: Text('Player',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                        DataColumn(
                          numeric: true,
                          label: Text('Score',
                              style: TextStyle(
                                  fontSize: 18, fontWeight: FontWeight.bold)),
                        ),
                      ],
                      rows: rankings.map((p) {
                        return DataRow(cells: [
                          DataCell(Text('${p['rank']}',
                              style: const TextStyle(fontSize: 16))),
                          DataCell(Text(p['username'] as String,
                              style: const TextStyle(fontSize: 16))),
                          DataCell(Text('${p['score']}',
                              style: const TextStyle(fontSize: 16))),
                        ]);
                      }).toList(),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
