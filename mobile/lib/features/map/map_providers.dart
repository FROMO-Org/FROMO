import 'package:flutter_riverpod/flutter_riverpod.dart';
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
}

final locationProvider = StateNotifierProvider<LocationNotifier, LocationState>(
  (_) => LocationNotifier(),
);

// Human-readable label for the current location, shown in the map top bar.
final cityNameProvider = FutureProvider.autoDispose<String>((ref) async {
  final pos = ref.watch(locationProvider).position;
  if (pos == null) return 'Locating…';
  try {
    final placemarks = await geo.placemarkFromCoordinates(pos.latitude, pos.longitude);
    if (placemarks.isNotEmpty) {
      final p = placemarks.first;
      final city = (p.locality?.isNotEmpty ?? false)
          ? p.locality!
          : (p.subAdministrativeArea ?? p.administrativeArea ?? '');
      final region = p.administrativeArea ?? p.country ?? '';
      if (city.isNotEmpty && region.isNotEmpty && city != region) return '$city, $region';
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
  final String? level; // 'busy' | 'moderate' | 'quiet'

  const BusynessArea({
    required this.id,
    required this.name,
    required this.lat,
    required this.lng,
    required this.radiusMetres,
    this.level,
  });

  factory BusynessArea.fromJson(Map<String, dynamic> j) => BusynessArea(
        id: j['id'] as String,
        name: j['name'] as String,
        lat: (j['lat'] as num).toDouble(),
        lng: (j['lng'] as num).toDouble(),
        radiusMetres: j['radius_metres'] as int,
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
      level: score?['level'] as String?,
    );
  }
}

final busynessAreasProvider = FutureProvider.autoDispose<List<BusynessArea>>((ref) async {
  final location = ref.watch(locationProvider);
  final api = ref.watch(apiClientProvider);
  // Heatmap is location-based; fall back to Manhattan, where the sample lives.
  final center = location.position ?? const LatLng(40.7580, -73.9855);

  try {
    final res = await api.get<Map<String, dynamic>>('/busyness/nearby', params: {
      'lat': center.latitude,
      'lng': center.longitude,
      'radius_km': 25,
    });
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
  BusynessArea(id: 'sample-times-square', name: 'Times Square', lat: 40.7580, lng: -73.9855, radiusMetres: 650, level: 'busy'),
  BusynessArea(id: 'sample-union-square', name: 'Union Square', lat: 40.7359, lng: -73.9911, radiusMetres: 550, level: 'busy'),
  BusynessArea(id: 'sample-greenwich', name: 'Greenwich Village', lat: 40.7336, lng: -74.0027, radiusMetres: 600, level: 'moderate'),
  BusynessArea(id: 'sample-lincoln', name: 'Lincoln Center', lat: 40.7725, lng: -73.9835, radiusMetres: 500, level: 'moderate'),
  BusynessArea(id: 'sample-les', name: 'Lower East Side', lat: 40.7180, lng: -73.9857, radiusMetres: 550, level: 'quiet'),
  BusynessArea(id: 'sample-fidi', name: 'Financial District', lat: 40.7068, lng: -74.0090, radiusMetres: 600, level: 'quiet'),
];

// ── Nearby Events ─────────────────────────────────────────────────────────────

final nearbyEventsProvider = FutureProvider.autoDispose<List<EventListItem>>((
  ref,
) async {
  final location = ref.watch(locationProvider);
  final api = ref.watch(apiClientProvider);

  // Try with location first; fall back to all events if nothing nearby
  if (location.position != null) {
    final res = await api.get<List<dynamic>>('/events/', params: {
      'status': 'active',
      'limit': 50,
      'lat': location.position!.latitude,
      'lng': location.position!.longitude,
      'radius_km': 20,
    });
    final nearby = (res.data ?? [])
        .cast<Map<String, dynamic>>()
        .map(EventListItem.fromJson)
        .toList();
    if (nearby.isNotEmpty) return nearby;
  }

  // No location or no nearby events → fetch all
  final res = await api.get<List<dynamic>>('/events/', params: {
    'status': 'active',
    'limit': 50,
  });
  final data = res.data ?? [];
  return data.cast<Map<String, dynamic>>().map(EventListItem.fromJson).toList();
});
