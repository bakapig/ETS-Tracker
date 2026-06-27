import 'package:flutter/material.dart';

import '../models/arrival.dart';

class ArrivalList extends StatelessWidget {
  const ArrivalList({super.key, required this.arrivals});

  final List<Arrival> arrivals;

  static Color _statusColor(BuildContext context, String status) {
    final scheme = Theme.of(context).colorScheme;
    return switch (status) {
      'on_time' => Colors.green.shade700,
      'delayed' => Colors.red.shade700,
      'early' => Colors.lightBlue.shade700,
      'live' => Colors.amber.shade800,
      _ => scheme.outline,
    };
  }

  static Color _statusBackground(BuildContext context, String status) {
    return switch (status) {
      'on_time' => Colors.green.withValues(alpha: 0.12),
      'delayed' => Colors.red.withValues(alpha: 0.12),
      'early' => Colors.lightBlue.withValues(alpha: 0.12),
      'live' => Colors.amber.withValues(alpha: 0.15),
      _ => Theme.of(context).colorScheme.surfaceContainerHighest,
    };
  }

  static String _statusLabel(Arrival arrival) {
    final status = arrival.status;
    final delay = arrival.delayMinutes;
    if (status == 'delayed' && delay != null) return 'Delayed $delay min';
    if (status == 'early' && delay != null) return '${delay.abs()} min early';
    if (status == 'live') return 'Live tracking';
    if (status == 'on_time') return 'On time';
    return 'Scheduled';
  }

  @override
  Widget build(BuildContext context) {
    if (arrivals.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
        decoration: BoxDecoration(
          border: Border.all(color: Theme.of(context).dividerColor),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          'No upcoming trains in the next 12 hours at this station.',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.outline,
              ),
        ),
      );
    }

    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          for (var i = 0; i < arrivals.length; i++) ...[
            if (i > 0) const Divider(height: 1),
            _ArrivalTile(arrival: arrivals[i]),
          ],
        ],
      ),
    );
  }
}

class _ArrivalTile extends StatelessWidget {
  const _ArrivalTile({required this.arrival});

  final Arrival arrival;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final displayTime = arrival.estimatedArrival ?? arrival.scheduledArrival;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      arrival.displayTrip,
                      style: theme.textTheme.titleSmall?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (arrival.isLive) ...[
                      const SizedBox(width: 8),
                      Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: Colors.red,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  '→ ${arrival.destination}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodyMedium,
                ),
                if (arrival.isLive)
                  Text(
                    'Live on map',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.amber.shade800,
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                displayTime,
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
              if (arrival.estimatedArrival != null)
                Text(
                  arrival.scheduledArrival,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.outline,
                    decoration: TextDecoration.lineThrough,
                  ),
                ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: ArrivalList._statusBackground(context, arrival.status),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  ArrivalList._statusLabel(arrival),
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: ArrivalList._statusColor(context, arrival.status),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
