import 'dart:async';

import 'package:flutter/material.dart';

import '../models/station.dart';
import '../services/api_client.dart';

const _popularStations = <({String label, String query})>[
  (label: 'KL Sentral', query: 'kl sentral'),
  (label: 'Kuala Lumpur', query: 'kuala lumpur'),
  (label: 'Ipoh', query: 'ipoh'),
  (label: 'Butterworth', query: 'butterworth'),
  (label: 'Padang Besar', query: 'padang besar'),
  (label: 'Gemas', query: 'gemas'),
];

class StationSearch extends StatefulWidget {
  const StationSearch({
    super.key,
    required this.api,
    required this.onSelect,
    this.selectedId,
  });

  final ApiClient api;
  final ValueChanged<Station> onSelect;
  final String? selectedId;

  @override
  State<StationSearch> createState() => _StationSearchState();
}

class _StationSearchState extends State<StationSearch> {
  final TextEditingController _controller = TextEditingController();
  List<Station> _results = [];
  bool _loading = false;
  bool _open = false;
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _runSearch(String query) async {
    setState(() => _loading = true);
    try {
      final data = await widget.api.searchStations(query);
      if (mounted) setState(() => _results = data);
    } catch (_) {
      if (mounted) setState(() => _results = []);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _scheduleSearch(String query) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () => _runSearch(query));
  }

  void _pick(Station station) {
    widget.onSelect(station);
    _controller.text = station.stopName;
    setState(() => _open = false);
  }

  Future<void> _pickPopular(String label, String query) async {
    _controller.text = label;
    setState(() => _open = true);
    try {
      final data = await widget.api.searchStations(query);
      if (data.isNotEmpty && mounted) _pick(data.first);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _controller,
          decoration: InputDecoration(
            hintText: 'Search station (e.g. KL Sentral, Ipoh…)',
            prefixIcon: const Icon(Icons.search),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          ),
          onTap: () => setState(() => _open = true),
          onChanged: (value) {
            setState(() => _open = true);
            _scheduleSearch(value);
          },
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _popularStations
              .map(
                (p) => ActionChip(
                  label: Text(p.label),
                  onPressed: () => _pickPopular(p.label, p.query),
                ),
              )
              .toList(),
        ),
        if (_open && (_controller.text.isNotEmpty || _results.isNotEmpty))
          Card(
            margin: const EdgeInsets.only(top: 8),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 240),
              child: _loading
                  ? const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('Searching…'),
                    )
                  : _results.isEmpty
                      ? const Padding(
                          padding: EdgeInsets.all(16),
                          child: Text('No stations found'),
                        )
                      : ListView.separated(
                          shrinkWrap: true,
                          itemCount: _results.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final station = _results[index];
                            final selected = widget.selectedId == station.stopId;
                            return ListTile(
                              selected: selected,
                              title: Text(station.stopName),
                              subtitle: Text('#${station.stopId}'),
                              onTap: () => _pick(station),
                            );
                          },
                        ),
            ),
          ),
      ],
    );
  }
}
