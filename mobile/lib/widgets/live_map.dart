import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../models/station.dart';
import '../models/vehicle.dart';
import '../services/api_client.dart';

class LiveMap extends StatefulWidget {
  const LiveMap({super.key, required this.station, required this.api});

  final Station? station;
  final ApiClient api;

  @override
  State<LiveMap> createState() => _LiveMapState();
}

class _LiveMapState extends State<LiveMap> {
  final MapController _mapController = MapController();
  List<Vehicle> _vehicles = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadVehicles();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _loadVehicles());
  }

  @override
  void didUpdateWidget(covariant LiveMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.station != null &&
        (oldWidget.station?.stopId != widget.station?.stopId)) {
      _recenter(widget.station!);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _mapController.dispose();
    super.dispose();
  }

  Future<void> _loadVehicles() async {
    try {
      final data = await widget.api.getVehicles();
      if (mounted) setState(() => _vehicles = data);
    } catch (_) {
      if (mounted) setState(() => _vehicles = []);
    }
  }

  void _recenter(Station station) {
    _mapController.move(
      LatLng(station.stopLat, station.stopLon),
      _mapController.camera.zoom,
    );
  }

  LatLng get _center {
    final station = widget.station;
    if (station != null) {
      return LatLng(station.stopLat, station.stopLon);
    }
    return const LatLng(4.5, 101.0);
  }

  double get _zoom => widget.station != null ? 10 : 7;

  @override
  Widget build(BuildContext context) {
    final station = widget.station;

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: SizedBox(
        height: 280,
        child: FlutterMap(
          mapController: _mapController,
          options: MapOptions(
            initialCenter: _center,
            initialZoom: _zoom,
            interactionOptions: const InteractionOptions(
              flags: InteractiveFlag.drag | InteractiveFlag.pinchZoom | InteractiveFlag.doubleTapZoom,
            ),
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.etslive.ets_live',
            ),
            if (station != null)
              MarkerLayer(
                markers: [
                  Marker(
                    point: LatLng(station.stopLat, station.stopLon),
                    width: 40,
                    height: 40,
                    child: const Icon(Icons.train, color: Colors.blueGrey, size: 32),
                  ),
                ],
              ),
            MarkerLayer(
              markers: _vehicles
                  .map(
                    (v) => Marker(
                      point: LatLng(v.latitude, v.longitude),
                      width: 36,
                      height: 36,
                      child: Tooltip(
                        message: [
                          v.label ?? v.vehicleId,
                          if (v.tripId != null) 'Trip: ${v.tripId}',
                          if (v.speedKmh != null) '${v.speedKmh!.round()} km/h',
                        ].join('\n'),
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.blue.shade700,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 2),
                            boxShadow: const [
                              BoxShadow(
                                color: Colors.black26,
                                blurRadius: 4,
                                offset: Offset(0, 2),
                              ),
                            ],
                          ),
                          alignment: Alignment.center,
                          child: const Text('🚆', style: TextStyle(fontSize: 14)),
                        ),
                      ),
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }
}
