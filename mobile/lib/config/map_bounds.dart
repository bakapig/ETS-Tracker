import 'package:latlong2/latlong.dart';

/// Peninsular + East Malaysia — keeps the map focused on KTMB coverage.
final malaysiaBounds = LatLngBounds(
  const LatLng(0.85, 99.0),
  const LatLng(7.8, 119.5),
);

const malaysiaCenter = LatLng(4.2, 109.0);

const mapMinZoom = 6.0;
const mapMaxZoom = 16.0;
const mapDefaultZoom = 7.0;
const mapStationZoom = 11.0;
