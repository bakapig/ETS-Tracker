import 'dart:async';

import 'package:flutter/material.dart';

import '../models/arrival.dart';
import '../models/station.dart';
import '../services/api_client.dart';
import '../widgets/ad_banner.dart';
import '../widgets/arrival_list.dart';
import '../widgets/live_map.dart';
import '../widgets/station_search.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Station? _station;
  List<Arrival> _arrivals = [];
  bool _loading = false;
  String? _error;
  Timer? _refreshTimer;

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadArrivals(Station station) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await widget.api.getArrivals(station.stopId);
      if (mounted) setState(() => _arrivals = data);
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Could not load arrivals. Is the backend running?';
          _arrivals = [];
        });
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _onSelectStation(Station station) {
    _refreshTimer?.cancel();
    setState(() => _station = station);
    _loadArrivals(station);
    _refreshTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _loadArrivals(station),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            Text(
              'Malaysia KTMB · Official GTFS',
              style: theme.textTheme.labelLarge?.copyWith(
                color: theme.colorScheme.primary,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'KTMB Live Malaysia',
              style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              'Live trains, station arrivals & delay estimates across Malaysia',
              style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.outline),
            ),
            const SizedBox(height: 20),
            StationSearch(
              api: widget.api,
              onSelect: _onSelectStation,
              selectedId: _station?.stopId,
            ),
            const SizedBox(height: 20),
            const AdBanner(slot: 'top-banner'),
            if (_station != null) ...[
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _station!.stopName,
                          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600),
                        ),
                        Text(
                          'Upcoming KTMB arrivals',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.outline,
                          ),
                        ),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: () => _loadArrivals(_station!),
                    child: const Text('Refresh'),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (_loading)
                Text('Loading arrivals…', style: theme.textTheme.bodySmall),
              if (_error != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.errorContainer,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _error!,
                    style: TextStyle(color: theme.colorScheme.onErrorContainer),
                  ),
                ),
              if (!_loading && _error == null) ArrivalList(arrivals: _arrivals),
            ],
            const SizedBox(height: 24),
            Text(
              'Live KTMB map',
              style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            LiveMap(station: _station, api: widget.api),
            const SizedBox(height: 4),
            Text(
              'All KTMB trains by category · refreshes every 30s',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
            ),
            const SizedBox(height: 20),
            const AdBanner(slot: 'bottom-banner'),
          ],
        ),
      ),
    );
  }
}
