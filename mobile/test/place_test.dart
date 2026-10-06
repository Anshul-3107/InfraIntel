import 'package:flutter_test/flutter_test.dart';
import 'package:geocoding/geocoding.dart';
import 'package:infraintel_app/place.dart';

void main() {
  test('uses a real landmark name when there is one', () {
    final place = placeNameFrom([
      Placemark(
        name: 'Bhopal Junction',
        thoroughfare: 'Hamidia Road',
        subLocality: 'Jahangirabad',
        locality: 'Bhopal',
        administrativeArea: 'Madhya Pradesh',
      ),
    ]);
    expect(place!.title, 'Near Bhopal Junction');
    expect(
      place.subtitle,
      'Hamidia Road, Jahangirabad, Bhopal, Madhya Pradesh',
    );
  });

  test('ignores a house number and uses the street', () {
    final place = placeNameFrom([
      Placemark(name: '42', thoroughfare: 'MG Road', locality: 'Indore'),
    ]);
    expect(place!.title, 'MG Road');
    expect(place.subtitle, 'Indore');
  });

  test('ignores a plus code and falls back to the area', () {
    final place = placeNameFrom([
      Placemark(name: 'VQ2J+X5', locality: 'Gwalior'),
    ]);
    expect(place!.title, 'Gwalior');
    expect(place.subtitle, isNull);
  });

  test('returns null when there is nothing usable', () {
    expect(placeNameFrom([]), isNull);
    expect(placeNameFrom([Placemark()]), isNull);
  });
}