import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:latlong2/latlong.dart';

import '../config/map_bounds.dart';
import '../config/vehicle_categories.dart';
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
  final Set<String> _hiddenRoutes = {};
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
      mapStationZoom,
    );
  }

  void _toggleRoute(String routeId) {
    setState(() {
      if (_hiddenRoutes.contains(routeId)) {
        _hiddenRoutes.remove(routeId);
      } else {
        _hiddenRoutes.add(routeId);
      }
    });
  }

  LatLng get _center {
    final station = widget.station;
    if (station != null) {
      return LatLng(station.stopLat, station.stopLon);
    }
    return malaysiaCenter;
  }

  double get _zoom => widget.station != null ? mapStationZoom : mapDefaultZoom;

  List<Vehicle> get _visibleVehicles => _vehicles
      .where((v) => !_hiddenRoutes.contains(v.routeId ?? 'unknown'))
      .toList();

  List<MapEntry<String, List<Vehicle>>> get _sortedRouteGroups {
    final grouped = groupVehiclesByRoute(_vehicles);
    final entries = grouped.entries.toList()
      ..sort((a, b) {
        final cmp = routeSortOrder(a.key).compareTo(routeSortOrder(b.key));
        if (cmp != 0) return cmp;
        final labelA = a.value.isNotEmpty ? routeGroupLabel(a.value.first) : a.key;
        final labelB = b.value.isNotEmpty ? routeGroupLabel(b.value.first) : b.key;
        return labelA.compareTo(labelB);
      });
    return entries;
  }

  @override
  Widget build(BuildContext context) {
    final station = widget.station;
    final routeGroups = _sortedRouteGroups;
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final entry in routeGroups)
              _RouteChip(
                routeId: entry.key,
                label: entry.value.isNotEmpty
                    ? routeGroupLabel(entry.value.first)
                    : entry.key,
                color: categoryMetaFor(entry.value.first).color,
                count: entry.value.length,
                hidden: _hiddenRoutes.contains(entry.key),
                onTap: () => _toggleRoute(entry.key),
              ),
          ],
        ),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: SizedBox(
            height: 280,
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: _center,
                initialZoom: _zoom,
                minZoom: mapMinZoom,
                maxZoom: mapMaxZoom,
                cameraConstraint: CameraConstraint.contain(bounds: malaysiaBounds),
                interactionOptions: const InteractionOptions(
                  flags: InteractiveFlag.drag |
                      InteractiveFlag.pinchZoom |
                      InteractiveFlag.doubleTapZoom,
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
                  markers: _visibleVehicles
                      .map(
                        (v) => Marker(
                          point: LatLng(v.latitude, v.longitude),
                          width: 36,
                          height: 36,
                          child: Tooltip(
                            message: [
                              v.displayTrip,
                              v.routeLabel,
                              if (v.speedKmh != null) formatSpeed(v.speedKmh),
                            ].join('\n'),
                            child: SvgPicture.asset(
                              trainIconAssetFor(v),
                              width: 32,
                              height: 32,
                            ),
                          ),
                        ),
                      )
                      .toList(),
                ),
              ],
            ),
          ),
        ),
        if (_vehicles.isNotEmpty) ...[
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(color: theme.dividerColor),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final entry in routeGroups)
                  if (!_hiddenRoutes.contains(entry.key))
                    _VehicleGroup(
                      label: entry.value.isNotEmpty
                          ? routeGroupLabel(entry.value.first)
                          : entry.key,
                      color: categoryMetaFor(entry.value.first).color,
                      vehicles: entry.value,
                    ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _RouteChip extends StatelessWidget {
  const _RouteChip({
    required this.routeId,
    required this.label,
    required this.color,
    required this.count,
    required this.hidden,
    required this.onTap,
  });

  final String routeId;
  final String label;
  final Color color;
  final int count;
  final bool hidden;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Text('$label ($count)', overflow: TextOverflow.ellipsis),
      selected: !hidden,
      onSelected: (_) => onTap(),
      avatar: CircleAvatar(
        radius: 6,
        backgroundColor: hidden ? Colors.grey.shade400 : color,
      ),
      showCheckmark: false,
    );
  }
}

class _VehicleGroup extends StatelessWidget {
  const _VehicleGroup({
    required this.label,
    required this.color,
    required this.vehicles,
  });

  final String label;
  final Color color;
  final List<Vehicle> vehicles;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(radius: 5, backgroundColor: color),
              const SizedBox(width: 8),
              Expanded(
                child: Text(label, style: theme.textTheme.titleSmall),
              ),
            ],
          ),
          const SizedBox(height: 6),
          for (final v in vehicles)
            Padding(
              padding: const EdgeInsets.only(left: 18, bottom: 4),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      v.displayTrip,
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
                  Text(
                    formatSpeed(v.speedKmh),
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
