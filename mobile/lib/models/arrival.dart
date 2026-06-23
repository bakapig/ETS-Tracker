class Arrival {
  const Arrival({
    required this.tripId,
    required this.routeShortName,
    required this.routeLongName,
    required this.destination,
    required this.scheduledArrival,
    required this.scheduledDeparture,
    this.estimatedArrival,
    this.delayMinutes,
    required this.status,
    required this.isLive,
    this.vehicleLabel,
  });

  final String tripId;
  final String routeShortName;
  final String routeLongName;
  final String destination;
  final String scheduledArrival;
  final String scheduledDeparture;
  final String? estimatedArrival;
  final int? delayMinutes;
  final String status;
  final bool isLive;
  final String? vehicleLabel;

  factory Arrival.fromJson(Map<String, dynamic> json) {
    return Arrival(
      tripId: json['trip_id'] as String,
      routeShortName: json['route_short_name'] as String,
      routeLongName: json['route_long_name'] as String,
      destination: json['destination'] as String,
      scheduledArrival: json['scheduled_arrival'] as String,
      scheduledDeparture: json['scheduled_departure'] as String,
      estimatedArrival: json['estimated_arrival'] as String?,
      delayMinutes: json['delay_minutes'] as int?,
      status: json['status'] as String,
      isLive: json['is_live'] as bool? ?? false,
      vehicleLabel: json['vehicle_label'] as String?,
    );
  }
}
