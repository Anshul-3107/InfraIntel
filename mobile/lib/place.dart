import 'dart:async';

import 'package:geocoding/geocoding.dart';

/// A human-readable description of a GPS position.
class PlaceName {
  const PlaceName({required this.title, this.subtitle});

  /// For example "Near Bhopal Junction" or "Hamidia Road".
  final String title;

  /// For example "Jahangirabad, Bhopal, Madhya Pradesh".
  final String? subtitle;

  /// One line to store on the server, for example
  /// "Near Bhopal Junction, Hamidia Road, Jahangirabad, Bhopal".
  /// Kept under 200 characters (the server allows 255).
  String get fullText {
    final text = subtitle == null ? title : '$title, $subtitle';
    return text.length <= 200 ? text : '${text.substring(0, 197)}...';
  }
}

// geocoding 5.x keeps its functions on a Geocoding instance.
final Geocoding _geocoding = Geocoding();

/// Looks up a place name for a position. Returns null when no name could
/// be found, there is no internet, or the phone has no geocoder.
Future<PlaceName?> lookupPlaceName(double latitude, double longitude) async {
  try {
    final marks = await _geocoding
        .placemarkFromCoordinates(latitude, longitude)
        .timeout(const Duration(seconds: 8));
    return placeNameFrom(marks);
  } catch (_) {
    return null;
  }
}

/// Picks the most useful description from the geocoder's answer.
/// A landmark is used only when it looks like a real name, not a house
/// number or a plus code like "VQ2J+X5".
PlaceName? placeNameFrom(List<Placemark> marks) {
  if (marks.isEmpty) return null;
  final p = marks.first;

  final street = _clean(p.thoroughfare) ?? _clean(p.street);
  final landmark = _landmark(_clean(p.name), street);

  final area = <String>[];
  for (final part in [p.subLocality, p.locality, p.administrativeArea]) {
    final c = _clean(part);
    if (c != null && c != landmark && c != street && !area.contains(c)) {
      area.add(c);
    }
  }

  final String title;
  final List<String> rest;
  if (landmark != null) {
    title = 'Near $landmark';
    rest = [?street, ...area];
  } else if (street != null) {
    title = street;
    rest = area;
  } else if (area.isNotEmpty) {
    title = area.first;
    rest = area.sublist(1);
  } else {
    return null;
  }

  return PlaceName(
    title: title,
    subtitle: rest.isEmpty ? null : rest.join(', '),
  );
}

String? _clean(String? value) {
  final v = value?.trim();
  return (v == null || v.isEmpty) ? null : v;
}

final _digitsOnly = RegExp(r'^[\d\s/\-,]+$');
final _plusCode = RegExp(r'^[0-9A-Z]{2,8}\+[0-9A-Z]{2,}$');
final _hasLetter = RegExp(r'\p{L}', unicode: true);

String? _landmark(String? name, String? street) {
  if (name == null || name.length < 3) return null;
  if (name == street) return null;
  if (_digitsOnly.hasMatch(name)) return null;
  if (_plusCode.hasMatch(name)) return null;
  if (!_hasLetter.hasMatch(name)) return null;
  return name;
}