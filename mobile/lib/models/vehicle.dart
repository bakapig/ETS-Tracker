class Vehicle {
  const Vehicle({
    required this.vehicleId,
    this.tripId,
    this.routeId,
    this.label,
    required this.latitude,
    required this.longitude,
    this.bearing,
    this.speedKmh,
    this.timestamp,
    this.occupancyStatus,
  });

  final String vehicleId;
  final String? tripId;
  final String? routeId;
  final String? label;
  final double latitude;
  final double longitude;
  final double? bearing;
  final double? speedKmh;
  final int? timestamp;
  final String? occupancyStatus;

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      vehicleId: json['vehicle_id'] as String,
      tripId: json['trip_id'] as String?,
      routeId: json['route_id'] as String?,
      label: json['label'] as String?,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      bearing: (json['bearing'] as num?)?.toDouble(),
      speedKmh: (json['speed_kmh'] as num?)?.toDouble(),
      timestamp: json['timestamp'] as int?,
      occupancyStatus: json['occupancy_status'] as String?,
    );
  }
}
