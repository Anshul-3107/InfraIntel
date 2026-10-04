import 'dart:io';

import 'package:flutter/material.dart';

import '../config.dart';
import '../models.dart';
import '../style.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({
    super.key,
    required this.imageFile,
    required this.inspection,
  });

  final File imageFile;
  final Inspection inspection;

  @override
  Widget build(BuildContext context) {
    final a = inspection.assessment;
    final h = inspection.health;
    final theme = Theme.of(context);
    final hasFaded = inspection.detections
        .any((d) => d.confidence < kScoringMinConfidence);

    return Scaffold(
      appBar: AppBar(title: Text('Inspection #${inspection.id}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: AspectRatio(
              aspectRatio: inspection.imageWidth / inspection.imageHeight,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Image.file(imageFile, fit: BoxFit.fill),
                  CustomPaint(
                    painter: DetectionPainter(
                      inspection.detections,
                      inspection.imageWidth,
                      inspection.imageHeight,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (hasFaded)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                'Faded boxes are low-confidence and not counted in the score.',
                style: theme.textTheme.bodySmall,
              ),
            ),
          const SizedBox(height: 16),
          _ScoreCard(
            title: 'Severity',
            score: a.score,
            level: a.priority,
            reasons: a.reasons,
          ),
          if (h != null) ...[
            const SizedBox(height: 12),
            _ScoreCard(
              title: 'Asset health',
              score: h.score,
              level: h.riskLevel,
              levelLabel: '${h.riskLevel} risk',
              subtitle:
                  'Trend: ${h.trend} · ${h.inspectionsConsidered} inspection(s) considered',
              reasons: h.reasons,
              footnote: inspection.assetAutoCreated
                  ? 'This location was registered as a new asset automatically.'
                  : null,
            ),
          ],
          const SizedBox(height: 16),
          Text('Detections (${inspection.detections.length})',
              style: theme.textTheme.titleMedium),
          const SizedBox(height: 4),
          if (inspection.detections.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Text('No damage detected.'),
            ),
          for (final d in inspection.detections)
            ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: CircleAvatar(
                radius: 8,
                backgroundColor: damageColor(d.type),
              ),
              title: Text(damageLabel(d.type)),
              trailing: Text(
                '${(d.confidence * 100).round()}%',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: d.confidence < kScoringMinConfidence
                      ? theme.disabledColor
                      : null,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ScoreCard extends StatelessWidget {
  const _ScoreCard({
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

class DetectionPainter extends CustomPainter {
  DetectionPainter(this.detections, this.imageWidth, this.imageHeight);

  final List<Detection> detections;
  final int imageWidth;
  final int imageHeight;

  @override
  void paint(Canvas canvas, Size size) {
    final sx = size.width / imageWidth;
    final sy = size.height / imageHeight;

    for (final d in detections) {
      final counted = d.confidence >= kScoringMinConfidence;
      final color = damageColor(d.type).withAlpha(counted ? 255 : 115);
      final rect = Rect.fromLTRB(
        d.box[0] * sx,
        d.box[1] * sy,
        d.box[2] * sx,
        d.box[3] * sy,
      );
      canvas.drawRect(
        rect,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = counted ? 2.5 : 1.2
          ..color = color,
      );

      if (!counted) continue;
      final tp = TextPainter(
        text: TextSpan(
          text: '${damageLabel(d.type)} ${(d.confidence * 100).round()}%',
          style: const TextStyle(
            color: Colors.black,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      final top = (rect.top - tp.height - 2).clamp(0.0, size.height - tp.height);
      final left = rect.left.clamp(0.0, size.width - tp.width - 6);
      canvas.drawRect(
        Rect.fromLTWH(left, top, tp.width + 6, tp.height + 2),
        Paint()..color = color,
      );
      tp.paint(canvas, Offset(left + 3, top + 1));
    }
  }

  @override
  bool shouldRepaint(covariant DetectionPainter old) =>
      old.detections != detections ||
      old.imageWidth != imageWidth ||
      old.imageHeight != imageHeight;
}