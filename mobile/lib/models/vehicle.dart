class Vehicle {
  const Vehicle({
    required this.vehicleId,
    this.tripId,
    this.serviceNumber,
    this.routeId,
    this.routeCategory,
    this.routeShortName,
    this.routeLongName,
    this.routeDisplayName,
    this.trainClass,
    this.trainClassLabel,
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
  final String? serviceNumber;
  final String? routeId;
  final String? routeCategory;
  final String? routeShortName;
  final String? routeLongName;
  final String? routeDisplayName;
  final String? trainClass;
  final String? trainClassLabel;
  final String? label;
  final double latitude;
  final double longitude;
  final double? bearing;
  final double? speedKmh;
  final int? timestamp;
  final String? occupancyStatus;

  String get routeLabel =>
      routeDisplayName ?? routeShortName ?? routeCategory ?? '—';

  String get displayTrip => serviceNumber ?? tripId ?? '—';

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      vehicleId: json['vehicle_id'] as String,
      tripId: json['trip_id'] as String?,
      serviceNumber: json['service_number'] as String?,
      routeId: json['route_id'] as String?,
      routeCategory: json['route_category'] as String?,
      routeShortName: json['route_short_name'] as String?,
      routeLongName: json['route_long_name'] as String?,
      routeDisplayName: json['route_display_name'] as String?,
      trainClass: json['train_class'] as String?,
      trainClassLabel: json['train_class_label'] as String?,
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
