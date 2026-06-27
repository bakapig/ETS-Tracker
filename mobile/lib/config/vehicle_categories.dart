import 'package:flutter/material.dart';

import '../models/vehicle.dart';

class VehicleCategoryMeta {
  const VehicleCategoryMeta({
    required this.key,
    required this.label,
    required this.color,
  });

  final String key;
  final String label;
  final Color color;
}

const vehicleCategoryOrder = [
  'ets',
  'komuter',
  'intercity',
  'shuttle',
  'other',
];

const vehicleCategories = <String, VehicleCategoryMeta>{
  'ets': VehicleCategoryMeta(key: 'ets', label: 'ETS', color: Color(0xFF2563EB)),
  'komuter': VehicleCategoryMeta(key: 'komuter', label: 'KTM Komuter', color: Color(0xFF16A34A)),
  'intercity': VehicleCategoryMeta(key: 'intercity', label: 'Intercity', color: Color(0xFFD97706)),
  'shuttle': VehicleCategoryMeta(key: 'shuttle', label: 'Intercity Shuttle', color: Color(0xFF7C3AED)),
  'other': VehicleCategoryMeta(key: 'other', label: 'Other', color: Color(0xFF71717A)),
};

VehicleCategoryMeta categoryMetaFor(Vehicle vehicle) {
  final key = vehicle.routeCategory ?? 'other';
  return vehicleCategories[key] ?? vehicleCategories['other']!;
}

const trainIconAssets = <String, String>{
  'ets': 'assets/trains/ets.svg',
  'komuter_83': 'assets/trains/komuter_83.svg',
  'komuter_92': 'assets/trains/komuter_92.svg',
  'dmu_61': 'assets/trains/dmu_61.svg',
  'intercity': 'assets/trains/intercity.svg',
  'default': 'assets/trains/default.svg',
};

String trainIconAssetFor(Vehicle vehicle) {
  final key = vehicle.trainClass;
  if (key != null && trainIconAssets.containsKey(key)) {
    return trainIconAssets[key]!;
  }
  return trainIconAssets['default']!;
}

String formatSpeed(double? speedKmh) {
  if (speedKmh == null) return '—';
  return '${speedKmh.toStringAsFixed(1)} km/h';
}

Map<String, List<Vehicle>> groupVehiclesByRoute(List<Vehicle> vehicles) {
  final groups = <String, List<Vehicle>>{};
  for (final vehicle in vehicles) {
    final key = vehicle.routeId ?? 'unknown';
    groups.putIfAbsent(key, () => []).add(vehicle);
  }
  return groups;
}

int routeSortOrder(String routeId) {
  const order = {
    'ETS': 0,
    '100_47300': 10,
    '100_9000': 11,
    'KA15_KD19': 12,
    'KC05_KB18': 13,
    'ERT': 20,
    'ES': 21,
    'SH': 30,
    'ST': 31,
  };
  return order[routeId] ?? 99;
}

String routeGroupLabel(Vehicle sample) => sample.routeLabel;

Map<String, List<Vehicle>> groupVehiclesByCategory(List<Vehicle> vehicles) {
  final groups = <String, List<Vehicle>>{
    for (final key in vehicleCategoryOrder) key: [],
  };
  for (final vehicle in vehicles) {
    final key = vehicle.routeCategory ?? 'other';
    (groups[key] ?? groups['other']!).add(vehicle);
  }
  return groups;
}
