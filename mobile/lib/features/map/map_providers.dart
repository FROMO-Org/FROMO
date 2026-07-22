import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart';
import 'package:geocoding/geocoding.dart' as geo;
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import '../../core/api_client.dart';
import '../../shared/models/event.dart';

// ── Location ──────────────────────────────────────────────────────────────────

class LocationState {
  final LatLng? position;
  final bool isLoading;
  final String? error;

  const LocationState({this.position, this.isLoading = false, this.error});

  LocationState copyWith({LatLng? position, bool? isLoading, String? error}) =>
      LocationState(
        position: position ?? this.position,
        isLoading: isLoading ?? this.isLoading,
        error: error ?? this.error,
      );
}

class LocationNotifier extends StateNotifier<LocationState> {
  LocationNotifier() : super(const LocationState());

  Future<void> requestLocation() async {
    const useDemoLocation = bool.fromEnvironment('USE_DEMO_LOCATION');
    if (kIsWeb && useDemoLocation) {
      state = state.copyWith(
        position: const LatLng(40.7580, -73.9855),
        isLoading: false,
        error: null,
      );
      return;
    }

    state = state.copyWith(isLoading: true, error: null);

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        state = state.copyWith(
          isLoading: false,
          error: 'Location services disabled',
        );
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          state = state.copyWith(
            isLoading: false,
            error: 'Location permission denied',
          );
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        state = state.copyWith(
          isLoading: false,
          error: 'Location permission permanently denied',
        );
        return;
      }

      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
      );

      state = state.copyWith(
        position: LatLng(pos.latitude, pos.longitude),
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setFallbackPosition(LatLng position) {
    if (state.position != null) return;
    state = state.copyWith(position: position, isLoading: false);
  }
}

final locationProvider = StateNotifierProvider<LocationNotifier, LocationState>(
  (_) => LocationNotifier(),
);

LatLng eventClusterCenter(List<EventListItem> events) {
  if (events.isEmpty) return const LatLng(40.7580, -73.9855);

  final buckets = <String, List<EventListItem>>{};
  for (final item in events) {
    final key =
        '${item.venue.lat.toStringAsFixed(2)},${item.venue.lng.toStringAsFixed(2)}';
    buckets.putIfAbsent(key, () => []).add(item);
  }

  final densest = buckets.values.reduce(
    (best, current) => current.length > best.length ? current : best,
  );

  final lat =
      densest.map((e) => e.venue.lat).reduce((a, b) => a + b) / densest.length;
  final lng =
      densest.map((e) => e.venue.lng).reduce((a, b) => a + b) / densest.length;
  return LatLng(lat, lng);
}

// Human-readable label for the current location, shown in the map top bar.
final cityNameProvider = FutureProvider.autoDispose<String>((ref) async {
  final pos = ref.watch(locationProvider).position;
  if (pos == null) return 'Locating…';
  try {
    final placemarks = await geo.placemarkFromCoordinates(
      pos.latitude,
      pos.longitude,
    );
    if (placemarks.isNotEmpty) {
      final p = placemarks.first;
      final city = (p.locality?.isNotEmpty ?? false)
          ? p.locality!
          : (p.subAdministrativeArea ?? p.administrativeArea ?? '');
      final region = p.administrativeArea ?? p.country ?? '';
      if (city.isNotEmpty && region.isNotEmpty && city != region) {
        return '$city, $region';
      }
      if (city.isNotEmpty) return city;
      if (region.isNotEmpty) return region;
    }
  } catch (_) {
    // Geocoding can fail offline or on emulators without a backend — fall back below.
  }
  return 'Current location';
});

// ── Busyness Areas ────────────────────────────────────────────────────────────

class BusynessArea {
  final String id;
  final String name;
  final double lat;
  final double lng;
  final int radiusMetres;
  final double? score;
  final String? level; // 'not busy' | 'as usual' | 'busier'

  const BusynessArea({
    required this.id,
    required this.name,
    required this.lat,
    required this.lng,
    required this.radiusMetres,
    this.score,
    this.level,
  });

  factory BusynessArea.fromJson(Map<String, dynamic> j) => BusynessArea(
    id: j['id'] as String,
    name: j['name'] as String,
    lat: (j['lat'] as num).toDouble(),
    lng: (j['lng'] as num).toDouble(),
    radiusMetres: j['radius_metres'] as int,
    score: (j['score'] as num?)?.toDouble(),
    level: j['level'] as String?,
  );

  // Shape returned by GET /busyness/nearby:
  // { area: { id, name, lat, lng, radius_metres, ... }, score: { level, ... }, distance_km }
  factory BusynessArea.fromNearbyJson(Map<String, dynamic> j) {
    final area = j['area'] as Map<String, dynamic>;
    final score = j['score'] as Map<String, dynamic>?;
    return BusynessArea(
      id: area['id'] as String,
      name: area['name'] as String,
      lat: (area['lat'] as num).toDouble(),
      lng: (area['lng'] as num).toDouble(),
      radiusMetres: area['radius_metres'] as int,
      score: (score?['score'] as num?)?.toDouble(),
      level: score?['level'] as String?,
    );
  }
}

final busynessAreasProvider = FutureProvider.autoDispose<List<BusynessArea>>((
  ref,
) async {
  final location = ref.watch(locationProvider);
  final api = ref.watch(apiClientProvider);
  // Heatmap is location-based; fall back to Manhattan, where the sample lives.
  final center = location.position ?? const LatLng(40.7580, -73.9855);

  try {
    final res = await api.get<Map<String, dynamic>>(
      '/busyness/nearby',
      params: {
        'lat': center.latitude,
        'lng': center.longitude,
        'radius_km': 25,
      },
    );
    final areas = (res.data?['areas'] as List?) ?? const [];
    final parsed = areas
        .cast<Map<String, dynamic>>()
        .map(BusynessArea.fromNearbyJson)
        .toList();
    if (parsed.isNotEmpty) return parsed;
  } catch (_) {
    // Endpoint unreachable or empty — fall through to the sample below.
  }

  // TEMP: the backend has no busyness data yet, so show a sample heatmap so the
  // feature is visible. Delete _sampleBusynessAreas once /busyness is populated.
  return _sampleBusynessAreas;
});

// TEMP sample heatmap data (Manhattan). Remove once the backend serves real data.
const _sampleBusynessAreas = <BusynessArea>[
  BusynessArea(
    id: 'sample-times-square',
    name: 'Times Square',
    lat: 40.7580,
    lng: -73.9855,
    radiusMetres: 650,
    level: 'busier',
  ),
  BusynessArea(
    id: 'sample-union-square',
    name: 'Union Square',
    lat: 40.7359,
    lng: -73.9911,
    radiusMetres: 550,
    level: 'busier',
  ),
  BusynessArea(
    id: 'sample-greenwich',
    name: 'Greenwich Village',
    lat: 40.7336,
    lng: -74.0027,
    radiusMetres: 600,
    level: 'as usual',
  ),
  BusynessArea(
    id: 'sample-lincoln',
    name: 'Lincoln Center',
    lat: 40.7725,
    lng: -73.9835,
    radiusMetres: 500,
    level: 'as usual',
  ),
  BusynessArea(
    id: 'sample-les',
    name: 'Lower East Side',
    lat: 40.7180,
    lng: -73.9857,
    radiusMetres: 550,
    level: 'not busy',
  ),
  BusynessArea(
    id: 'sample-fidi',
    name: 'Financial District',
    lat: 40.7068,
    lng: -74.0090,
    radiusMetres: 600,
    level: 'not busy',
  ),
];

// ── Nearby Events ─────────────────────────────────────────────────────────────

final nearbyEventsProvider = FutureProvider.autoDispose<List<EventListItem>>((
  ref,
) async {
  final location = ref.watch(locationProvider);
  final api = ref.watch(apiClientProvider);

  // Try with location first; fall back to all events if nothing nearby or if
  // the location-scoped request fails on a constrained mobile browser.
  if (location.position != null) {
    try {
      final res = await api.get<List<dynamic>>(
        '/events/',
        params: {
          'status': 'active',
          'limit': 50,
          'lat': location.position!.latitude,
          'lng': location.position!.longitude,
          'radius_km': 20,
        },
      );
      final nearby = (res.data ?? [])
          .cast<Map<String, dynamic>>()
          .map(EventListItem.fromJson)
          .toList();
      if (nearby.isNotEmpty) return _withVenueAccessibility(api, nearby);
    } catch (_) {
      // Continue to the all-events fallback below.
    }
  }

  try {
    // No location or no nearby events -> fetch all
    final res = await api.get<List<dynamic>>(
      '/events/',
      params: {'status': 'active', 'limit': 50},
    );
    final data = res.data ?? [];
    final items = data
        .cast<Map<String, dynamic>>()
        .map(EventListItem.fromJson)
        .toList();
    return _withVenueAccessibility(api, items);
  } catch (_) {
    return const [];
  }
});

Future<List<EventListItem>> _withVenueAccessibility(
  ApiClient api,
  List<EventListItem> items,
) async {
  if (items.isEmpty) return items;

  try {
    final venueIds = items.map((item) => item.venue.id).toSet();
    final venueById = <String, Map<String, dynamic>>{};

    for (final venueId in venueIds) {
      try {
        final res = await api.get<Map<String, dynamic>>('/venues/$venueId');
        if (res.data != null) venueById[venueId] = res.data!;
      } catch (_) {
        // Keep the embedded venue summary if a specific venue cannot be loaded.
      }
    }

    return items
        .map(
          (item) => item.copyWith(
            venue: item.venue.copyWith(
              category: venueById[item.venue.id]?['category'] as String?,
              isAccessible:
                  venueById[item.venue.id]?['is_accessible'] as bool? ??
                  item.venue.isAccessible,
            ),
          ),
        )
        .toList();
  } catch (_) {
    return items;
  }
}
