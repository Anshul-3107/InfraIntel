import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../actions.dart';
import '../config.dart';
import '../models.dart';
import '../style.dart';
import '../widgets.dart';

/// Shows one inspection. [image] is a local file right after upload
/// and the server's copy when opened from History.
class ResultScreen extends ConsumerWidget {
  const ResultScreen({
    super.key,
    required this.image,
    required this.inspection,
  });

  final ImageProvider image;
  final Inspection inspection;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final a = inspection.assessment;
    final h = inspection.health;
    final theme = Theme.of(context);
    final hasFaded = inspection.detections
        .any((d) => d.confidence < kScoringMinConfidence);

    return Scaffold(
      appBar: AppBar(
        title: Text('Inspection #${inspection.id}'),
        actions: [
          IconButton(
            tooltip: 'Delete inspection',
            icon: const Icon(Icons.delete_outline),
            onPressed: () async {
              final deleted =
                  await confirmAndDeleteInspection(context, ref, inspection);
              if (deleted && context.mounted) Navigator.of(context).pop();
            },
          ),
        ],
      ),
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
                  Image(image: image, fit: BoxFit.fill),
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
          const SizedBox(height: 8),
          Text(
            '${formatDateTime(inspection.createdAt)} · ${inspection.assetLabel}',
            style: theme.textTheme.bodySmall,
          ),
          if (hasFaded)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                'Faded boxes are low-confidence and not counted in the score.',
                style: theme.textTheme.bodySmall,
              ),
            ),
          const SizedBox(height: 16),
          ScoreCard(
            title: 'Severity',
            score: a.score,
            level: a.priority,
            reasons: a.reasons,
          ),
          if (h != null) ...[
            const SizedBox(height: 12),
            ScoreCard(
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