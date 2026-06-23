class Station {
  const Station({
    required this.stopId,
    required this.stopName,
    required this.stopLat,
    required this.stopLon,
  });

  final String stopId;
  final String stopName;
  final double stopLat;
  final double stopLon;

  factory Station.fromJson(Map<String, dynamic> json) {
    return Station(
      stopId: json['stop_id'] as String,
      stopName: json['stop_name'] as String,
      stopLat: (json['stop_lat'] as num).toDouble(),
      stopLon: (json['stop_lon'] as num).toDouble(),
    );
  }
}
