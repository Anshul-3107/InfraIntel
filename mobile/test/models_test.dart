import 'package:flutter_test/flutter_test.dart';
import 'package:infraintel_app/models.dart';

void main() {
  test('Inspection parses the API response', () {
    final json = {
      'id': 3,
      'inspector': 'inspector1',
      'image': 'http://127.0.0.1:8000/media/inspections/2026/10/a.jpg',
      'latitude': 23.2599,
      'longitude': 77.4126,
      'image_width': 720,
      'image_height': 720,
      'num_detections': 2,
      'created_at': '2026-10-04T18:50:12.793199Z',
      'assessment': {
        'version': 'severity-v1',
        'severity_score': 50,
        'priority': 'HIGH',
        'coverage_pct': {'alligator_crack': 48.6, 'pothole': 0.73},
        'score_breakdown': {'alligator_crack': 40.0},
        'reasons': ['Alligator cracking over 49% of the frame (1 region)'],
        'ignored_low_confidence': 3,
      },
      'infrastructure': {'id': 1, 'name': '', 'auto_created': true},
      'asset_health': {
        'version': 'health-v1',
        'health_score': 45,
        'risk_level': 'HIGH',
        'trend': 'stable',
        'reasons': ['Latest inspection severity 50/100'],
        'inspections_considered': 2,
      },
      'detections': [
        {
          'damage_type': 'alligator_crack',
          'confidence': 0.663,
          'bounding_box': [201.0, 233.5, 720.0, 720.0],
          'source_model': 'crack_model',
        },
        {
          'damage_type': 'pothole',
          'confidence': 0.538,
          'bounding_box': [123.4, 308.9, 175.1, 345.4],
          'source_model': 'pothole_model',
        },
      ],
    };

    final i = Inspection.fromJson(json);
    expect(i.id, 3);
    expect(i.assessment.score, 50);
    expect(i.assessment.priority, 'HIGH');
    expect(i.detections.length, 2);
    expect(i.detections.first.box.last, 720.0);
    expect(i.health!.score, 45);
    expect(i.assetId, 1);
    expect(i.assetLabel, 'Asset #1');
    expect(i.assetAutoCreated, isTrue);
    expect(i.createdAt.isUtc, isTrue);
  });

  test('Asset parses with and without health', () {
    final withHealth = Asset.fromJson({
      'id': 2,
      'name': 'Bhopal bypass',
      'asset_type': 'road',
      'latitude': 23.26,
      'longitude': 77.41,
      'construction_year': 2005,
      'auto_created': false,
      'health': {
        'version': 'health-v1',
        'health_score': 60,
        'risk_level': 'MEDIUM',
        'trend': 'stable',
        'reasons': ['Latest inspection severity 40/100'],
        'inspections_considered': 1,
      },
      'recent_inspections': [
        {
          'id': 9,
          'created_at': '2026-10-04T18:50:12Z',
          'severity_score': 40,
          'priority': 'MEDIUM',
        },
      ],
    });
    expect(withHealth.label, 'Bhopal bypass');
    expect(withHealth.constructionYear, 2005);
    expect(withHealth.health!.riskLevel, 'MEDIUM');
    expect(withHealth.recent.single.severityScore, 40);

    final noHealth = Asset.fromJson({
      'id': 3,
      'name': '',
      'asset_type': 'road',
      'latitude': 1.0,
      'longitude': 2.0,
      'construction_year': null,
      'auto_created': true,
      'health': null,
      'recent_inspections': [],
    });
    expect(noHealth.label, 'Asset #3');
    expect(noHealth.health, isNull);
  });
}