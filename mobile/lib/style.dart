import 'package:flutter/material.dart';

/// Colours match ml/config.py DAMAGE_COLORS (converted from BGR to RGB).
Color damageColor(String type) {
  switch (type) {
    case 'pothole':
      return const Color(0xFFE53935);
    case 'longitudinal_crack':
      return const Color(0xFFFDD835);
    case 'transverse_crack':
      return const Color(0xFFD81B60);
    case 'alligator_crack':
      return const Color(0xFFFB8C00);
    default:
      return Colors.white;
  }
}

String damageLabel(String type) {
  switch (type) {
    case 'pothole':
      return 'Pothole';
    case 'longitudinal_crack':
      return 'Longitudinal crack';
    case 'transverse_crack':
      return 'Transverse crack';
    case 'alligator_crack':
      return 'Alligator crack';
    default:
      return type;
  }
}

/// Used for both priority (LOW..CRITICAL) and asset risk level.
Color levelColor(String level) {
  switch (level) {
    case 'LOW':
      return const Color(0xFF2E7D32);
    case 'MEDIUM':
      return const Color(0xFFF9A825);
    case 'HIGH':
      return const Color(0xFFEF6C00);
    case 'CRITICAL':
      return const Color(0xFFC62828);
    default:
      return Colors.grey;
  }
}