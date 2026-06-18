import 'package:flutter_riverpod/flutter_riverpod.dart';
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
}

final busynessAreasProvider = FutureProvider.autoDispose<List<BusynessArea>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final res = await api.get<List<dynamic>>('/busyness-areas/');
  final data = res.data ?? [];
  return data.cast<Map<String, dynamic>>().map(BusynessArea.fromJson).toList();
});

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
