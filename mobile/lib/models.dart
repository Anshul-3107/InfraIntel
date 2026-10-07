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
    required this.imageUrl,
    required this.latitude,
    required this.longitude,
    required this.locationName,
    required this.createdAt,
    required this.inspector,
    required this.imageWidth,
    required this.imageHeight,
    required this.detections,
    required this.assessment,
    required this.health,
    required this.assetId,
    required this.assetName,
    required this.assetLocation,
    required this.assetAutoCreated,
  });

  final int id;
  final String imageUrl;
  final double latitude;
  final double longitude;

  /// Where this photo was taken, as reported by the phone. May be empty.
  final String locationName;
  final DateTime createdAt;
  final String? inspector;
  final int imageWidth;
  final int imageHeight;
  final List<Detection> detections;
  final Assessment assessment;
  final AssetHealth? health;
  final int? assetId;

  /// Name set by staff in the dashboard. May be empty.
  final String assetName;

  /// Place name recorded when the asset was first inspected. May be empty.
  final String assetLocation;
  final bool assetAutoCreated;

  /// Staff name, else the asset's place name, else "Asset #id".
  String get assetLabel {
    if (assetId == null) return 'No asset';
    if (assetName.isNotEmpty) return assetName;
    if (assetLocation.isNotEmpty) return assetLocation;
    return 'Asset #$assetId';
  }

  factory Inspection.fromJson(Map<String, dynamic> j) {
    final asset = j['infrastructure'] as Map<String, dynamic>?;
    final health = j['asset_health'] as Map<String, dynamic>?;
    return Inspection(
      id: (j['id'] as num).toInt(),
      imageUrl: j['image'] as String,
      latitude: (j['latitude'] as num).toDouble(),
      longitude: (j['longitude'] as num).toDouble(),
      locationName: j['location_name'] as String? ?? '',
      createdAt: DateTime.parse(j['created_at'] as String),
      inspector: j['inspector'] as String?,
      imageWidth: (j['image_width'] as num).toInt(),
      imageHeight: (j['image_height'] as num).toInt(),
      detections: (j['detections'] as List)
          .map((d) => Detection.fromJson(d as Map<String, dynamic>))
          .toList(),
      assessment:
          Assessment.fromJson(j['assessment'] as Map<String, dynamic>),
      health: health == null ? null : AssetHealth.fromJson(health),
      assetId: asset == null ? null : (asset['id'] as num).toInt(),
      assetName: asset == null ? '' : (asset['name'] as String? ?? ''),
      assetLocation:
          asset == null ? '' : (asset['location_name'] as String? ?? ''),
      assetAutoCreated:
          asset == null ? false : (asset['auto_created'] as bool? ?? false),
    );
  }
}

class RecentInspection {
  const RecentInspection({
    required this.id,
    required this.createdAt,
    required this.severityScore,
    required this.priority,
  });

  final int id;
  final DateTime createdAt;
  final int severityScore;
  final String priority;

  factory RecentInspection.fromJson(Map<String, dynamic> j) => RecentInspection(
        id: (j['id'] as num).toInt(),
        createdAt: DateTime.parse(j['created_at'] as String),
        severityScore: (j['severity_score'] as num).toInt(),
        priority: j['priority'] as String,
      );
}

class Asset {
  const Asset({
    required this.id,
    required this.name,
    required this.locationName,
    required this.assetType,
    required this.latitude,
    required this.longitude,
    required this.constructionYear,
    required this.autoCreated,
    required this.health,
    required this.recent,
  });

  final int id;

  /// Name set by staff in the dashboard. May be empty.
  final String name;

  /// Place name recorded when the asset was first inspected. May be empty.
  final String locationName;
  final String assetType;
  final double latitude;
  final double longitude;
  final int? constructionYear;
  final bool autoCreated;
  final AssetHealth? health;
  final List<RecentInspection> recent;

  /// Staff name, else the place name, else "Asset #id".
  String get label {
    if (name.isNotEmpty) return name;
    if (locationName.isNotEmpty) return locationName;
    return 'Asset #$id';
  }

  factory Asset.fromJson(Map<String, dynamic> j) {
    final health = j['health'] as Map<String, dynamic>?;
    return Asset(
      id: (j['id'] as num).toInt(),
      name: j['name'] as String? ?? '',
      locationName: j['location_name'] as String? ?? '',
      assetType: j['asset_type'] as String? ?? 'road',
      latitude: (j['latitude'] as num).toDouble(),
      longitude: (j['longitude'] as num).toDouble(),
      constructionYear: (j['construction_year'] as num?)?.toInt(),
      autoCreated: j['auto_created'] as bool? ?? false,
      health: health == null ? null : AssetHealth.fromJson(health),
      recent: ((j['recent_inspections'] as List?) ?? const [])
          .map((r) => RecentInspection.fromJson(r as Map<String, dynamic>))
          .toList(),
    );
  }
}