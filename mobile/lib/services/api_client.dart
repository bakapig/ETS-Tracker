import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../models/arrival.dart';
import '../models/station.dart';
import '../models/vehicle.dart';

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('${ApiConfig.baseUrl}$path').replace(queryParameters: query);
  }

  Future<T> _fetchJson<T>(
    String path, {
    Map<String, String>? query,
    required T Function(dynamic json) parse,
  }) async {
    final response = await _client.get(_uri(path, query));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(response.statusCode, path);
    }
    return parse(jsonDecode(response.body));
  }

  Future<List<Station>> searchStations(String query) {
    return _fetchJson(
      '/api/stations',
      query: {'q': query, 'ets_only': 'true'},
      parse: (json) =>
          (json as List).map((e) => Station.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Future<Station> getStation(String stopId) {
    return _fetchJson(
      '/api/stations/$stopId',
      parse: (json) => Station.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<List<Arrival>> getArrivals(String stopId, {int limit = 10}) {
    return _fetchJson(
      '/api/stations/$stopId/arrivals',
      query: {'limit': '$limit'},
      parse: (json) =>
          (json as List).map((e) => Arrival.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Future<List<Vehicle>> getVehicles() {
    return _fetchJson(
      '/api/vehicles',
      query: {'ets_only': 'true'},
      parse: (json) =>
          (json as List).map((e) => Vehicle.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
}

class ApiException implements Exception {
  ApiException(this.statusCode, this.path);

  final int statusCode;
  final String path;

  @override
  String toString() => 'API error $statusCode: $path';
}
