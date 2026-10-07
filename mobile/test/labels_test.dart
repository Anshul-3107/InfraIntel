import 'package:flutter_test/flutter_test.dart';
import 'package:infraintel_app/models.dart';
import 'package:infraintel_app/place.dart';

Map<String, dynamic> inspectionJson(Map<String, dynamic>? infrastructure) => {
      'id': 1,
      'image': 'http://127.0.0.1:8000/media/a.jpg',
      'latitude': 23.26,
      'longitude': 77.41,
      'location_name': 'Near the bridge',
      'created_at': '2026-10-04T18:50:12Z',
      'inspector': 'inspector1',
      'image_width': 100,
      'image_height': 100,
      'assessment': {
        'severity_score': 0,
        'priority': 'LOW',
        'reasons': <String>[],
        'coverage_pct': <String, double>{},
      },
      'infrastructure': infrastructure,
      'asset_health': null,
      'detections': <Map<String, dynamic>>[],
    };

Map<String, dynamic> assetJson({String name = '', String locationName = ''}) => {
      'id': 7,
      'name': name,
      'location_name': locationName,
      'asset_type': 'road',
      'latitude': 23.26,
      'longitude': 77.41,
      'construction_year': null,
      'auto_created': true,
      'health': null,
      'recent_inspections': <Map<String, dynamic>>[],
    };

void main() {
  group('Inspection.assetLabel', () {
    test('staff name wins over the place name', () {
      final i = Inspection.fromJson(inspectionJson({
        'id': 3,
        'name': 'Ring Road',
        'location_name': 'Near Bhopal Junction',
        'auto_created': false,
      }));
      expect(i.assetLabel, 'Ring Road');
    });

    test('uses the place name when there is no staff name', () {
      final i = Inspection.fromJson(inspectionJson({
        'id': 3,
        'name': '',
        'location_name': 'Near Bhopal Junction',
        'auto_created': true,
      }));
      expect(i.assetLabel, 'Near Bhopal Junction');
    });

    test('falls back to the asset id', () {
      final i = Inspection.fromJson(inspectionJson({
        'id': 3,
        'name': '',
        'location_name': '',
        'auto_created': true,
      }));
      expect(i.assetLabel, 'Asset #3');
    });

    test('an older response without location_name still parses', () {
      final i = Inspection.fromJson(inspectionJson({
        'id': 3,
        'name': '',
        'auto_created': true,
      }));
      expect(i.assetLabel, 'Asset #3');
    });

    test('no asset', () {
      expect(Inspection.fromJson(inspectionJson(null)).assetLabel, 'No asset');
    });

    test('the photo\'s own place name is kept', () {
      final i = Inspection.fromJson(inspectionJson(null));
      expect(i.locationName, 'Near the bridge');
    });
  });

  group('Asset.label', () {
    test('staff name wins', () {
      expect(
        Asset.fromJson(assetJson(name: 'Ring Road', locationName: 'Bhopal')).label,
        'Ring Road',
      );
    });

    test('place name when there is no staff name', () {
      expect(Asset.fromJson(assetJson(locationName: 'Bhopal')).label, 'Bhopal');
    });

    test('asset id as the last resort', () {
      expect(Asset.fromJson(assetJson()).label, 'Asset #7');
    });
  });

  group('PlaceName.fullText', () {
    test('joins title and subtitle', () {
      const place = PlaceName(
        title: 'Near Bhopal Junction',
        subtitle: 'Hamidia Road, Bhopal',
      );
      expect(place.fullText, 'Near Bhopal Junction, Hamidia Road, Bhopal');
    });

    test('title only', () {
      expect(const PlaceName(title: 'Hamidia Road').fullText, 'Hamidia Road');
    });

    test('is cut to 200 characters', () {
      final place = PlaceName(title: 'a' * 300);
      expect(place.fullText.length, 200);
      expect(place.fullText.endsWith('...'), isTrue);
    });
  });
}