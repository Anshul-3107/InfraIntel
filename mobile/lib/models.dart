class Detection {
  const Detection({
    required this.type,
    required this.confidence,
    required this.box,
    required this.sourceModel,
  });

  final String type;
  final double confidence;

  /// Pixel coordinates in the server's image: xmin, ymin, xmax, ymax.
  final List<double> box;
  final String sourceModel;

  factory Detection.fromJson(Map<String, dynamic> j) => Detection(
        type: j['damage_type'] as String,
        confidence: (j['confidence'] as num).toDouble(),
        box: (j['bounding_box'] as List)
            .map((v) => (v as num).toDouble())
            .toList(),
        sourceModel: j['source_model'] as String,
      );
}

List<String> _strings(dynamic list) =>
    (list as List).map((e) => e.toString()).toList();

class Assessment {
  const Assessment({
    required this.score,
    required this.priority,
    required this.reasons,
    required this.coveragePct,
  });

  final int score;
  final String priority;
  final List<String> reasons;
  final Map<String, double> coveragePct;

  factory Assessment.fromJson(Map<String, dynamic> j) => Assessment(
        score: (j['severity_score'] as num).toInt(),
        priority: j['priority'] as String,
        reasons: _strings(j['reasons']),
        coveragePct: (j['coverage_pct'] as Map).map(
          (k, v) => MapEntry(k as String, (v as num).toDouble()),
        ),
      );
}

class AssetHealth {
  const AssetHealth({
    required this.score,
    required this.riskLevel,
    required this.trend,
    required this.reasons,
    required this.inspectionsConsidered,
  });

  final int score;
  final String riskLevel;
  final String trend;
  final List<String> reasons;
  final int inspectionsConsidered;

  factory AssetHealth.fromJson(Map<String, dynamic> j) => AssetHealth(
        score: (j['health_score'] as num).toInt(),
        riskLevel: j['risk_level'] as String,
        trend: j['trend'] as String,
        reasons: _strings(j['reasons']),
        inspectionsConsidered: (j['inspections_considered'] as num).toInt(),
      );
}

class Inspection {
  const Inspection({
    required this.id,
    required this.imageWidth,
    required this.imageHeight,
    required this.detections,
    required this.assessment,
    required this.health,
    required this.assetId,
    required this.assetAutoCreated,
  });

  final int id;
  final int imageWidth;
  final int imageHeight;
  final List<Detection> detections;
  final Assessment assessment;
  final AssetHealth? health;
  final int? assetId;
  final bool assetAutoCreated;

  factory Inspection.fromJson(Map<String, dynamic> j) {
    final asset = j['infrastructure'] as Map<String, dynamic>?;
    final health = j['asset_health'] as Map<String, dynamic>?;
    return Inspection(
      id: (j['id'] as num).toInt(),
      imageWidth: (j['image_width'] as num).toInt(),
      imageHeight: (j['image_height'] as num).toInt(),
      detections: (j['detections'] as List)
          .map((d) => Detection.fromJson(d as Map<String, dynamic>))
          .toList(),
      assessment:
          Assessment.fromJson(j['assessment'] as Map<String, dynamic>),
      health: health == null ? null : AssetHealth.fromJson(health),
      assetId: asset == null ? null : (asset['id'] as num).toInt(),
      assetAutoCreated:
          asset == null ? false : (asset['auto_created'] as bool? ?? false),
    );
  }
}