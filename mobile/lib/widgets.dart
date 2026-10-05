import 'package:flutter/material.dart';

import 'style.dart';

/// "5 Oct 2026, 3:57 pm" in the phone's local time.
String formatDateTime(DateTime dt) {
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
  ];
  final d = dt.toLocal();
  final hour12 = d.hour % 12 == 0 ? 12 : d.hour % 12;
  final minute = d.minute.toString().padLeft(2, '0');
  final suffix = d.hour >= 12 ? 'pm' : 'am';
  return '${d.day} ${months[d.month - 1]} ${d.year}, $hour12:$minute $suffix';
}

/// Small coloured label for LOW / MEDIUM / HIGH / CRITICAL.
class LevelTag extends StatelessWidget {
  const LevelTag(this.level, {super.key});

  final String level;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: levelColor(level),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        level,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class ScoreCard extends StatelessWidget {
  const ScoreCard({
    super.key,
    required this.title,
    required this.score,
    required this.level,
    required this.reasons,
    this.levelLabel,
    this.subtitle,
    this.footnote,
  });

  final String title;
  final int score;
  final String level;
  final String? levelLabel;
  final String? subtitle;
  final String? footnote;
  final List<String> reasons;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = levelColor(level);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 72,
                  height: 72,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: color, width: 5),
                  ),
                  child: Text(
                    '$score',
                    style: theme.textTheme.headlineSmall
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: theme.textTheme.labelLarge),
                      Text(
                        levelLabel ?? level,
                        style: theme.textTheme.titleLarge?.copyWith(
                          color: color,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (subtitle != null)
                        Text(subtitle!, style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            for (final r in reasons)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text('• $r'),
              ),
            if (footnote != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(footnote!, style: theme.textTheme.bodySmall),
              ),
          ],
        ),
      ),
    );
  }
}