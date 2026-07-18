import 'dart:math' as math;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';
import 'package:latlong2/latlong.dart' as ll;
import 'package:url_launcher/url_launcher.dart';
import '../../core/constants.dart';
import '../../core/theme.dart';
import '../../shared/models/event.dart';
import 'map_providers.dart';

const _allCategoryFilter = 'All';
const _searchRadiusKm = 1.0;
const _initialMapZoom = 15.4;
const _focusedMapZoom = 16.2;
const _singleEventZoom = 16.1;
const _midClusterZoom = 14.5;

class _CrowdBadgeData {
  final String label;
  final Color color;
  final Color glowColor;

  const _CrowdBadgeData({
    required this.label,
    required this.color,
    required this.glowColor,
  });
}

class _PinLayout {
  final EventListItem item;
  final Offset offset;
  final int siblingCount;

  const _PinLayout({
    required this.item,
    required this.offset,
    required this.siblingCount,
  });
}

class _EventCluster {
  final LatLng center;
  final List<EventListItem> items;

  const _EventCluster({required this.center, required this.items});

  bool get isSingle => items.length == 1;
}

class _MapScopeData {
  final List<EventListItem> visibleItems;
  final List<BusynessArea> visibleAreas;

  const _MapScopeData({required this.visibleItems, required this.visibleAreas});
}

String? _categoryForItem(EventListItem item) =>
    item.event.category ?? item.venue.category;

String _categoryKey(String? category) {
  final normalized = (category ?? '').trim().toLowerCase();
  if (normalized == 'sports') return 'sport';
  if (normalized == 'arts' || normalized == 'arts and theatre') {
    return 'art';
  }
  return normalized.replaceAll(RegExp(r'\s+'), ' ');
}

String _categoryLabel(String category) {
  final trimmed = category.trim();
  if (trimmed.isEmpty) return trimmed;
  return trimmed
      .split(RegExp(r'\s+'))
      .map((word) {
        if (word == '&') return word;
        if (word.length <= 2) return word.toUpperCase();
        return word[0].toUpperCase() + word.substring(1).toLowerCase();
      })
      .join(' ');
}

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  final _mapController = MapController();
  String? _selectedEventId;
  String _activeFilter = _allCategoryFilter;
  bool _showAllEvents = false;
  bool _accessibleOnly = false;
  bool _mapCenteredOnEvents = false;
  bool _mapCenteredOnLocation = false;
  double _currentZoom = _initialMapZoom;
  List<LatLng> _routePoints = const [];
  String? _routeEventId;
  String? _routeLoadingEventId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(locationProvider.notifier).requestLocation();
    });
  }

  void _centerOnEventsIfNeeded(List<EventListItem> events) {
    // Only auto-pan once, and only if we have no real nearby events (distanceKm is null)
    if (_mapCenteredOnEvents) return;
    if (events.isEmpty) return;
    final hasNearby = events.any((e) => e.distanceKm != null);
    if (hasNearby) return; // user is near events, map is already correct
    _mapCenteredOnEvents = true;
    final center = eventClusterCenter(events);
    ref.read(locationProvider.notifier).setFallbackPosition(center);
    _mapController.move(center, _initialMapZoom);
  }

  @override
  void dispose() {
    _mapController.dispose();
    super.dispose();
  }

  List<EventListItem> _upcomingEvents(List<EventListItem> items) {
    return items.where((item) => !item.event.isPast).toList();
  }

  List<EventListItem> _applyFilter(List<EventListItem> items) {
    final upcomingItems = _upcomingEvents(items);
    final categoryFilteredItems = _activeFilter == _allCategoryFilter
        ? upcomingItems
        : upcomingItems
              .where(
                (i) =>
                    _categoryKey(_categoryForItem(i)) ==
                    _categoryKey(_activeFilter),
              )
              .toList();
    if (!_accessibleOnly) return categoryFilteredItems;
    return categoryFilteredItems
        .where((item) => item.venue.isAccessible)
        .toList();
  }

  List<EventListItem> _eventsWithinRadius(
    List<EventListItem> items,
    LatLng? center,
    double radiusKm,
  ) {
    if (center == null) return items;
    final distance = ll.Distance();
    return items.where((item) {
      final km =
          item.distanceKm ??
          distance.as(
            ll.LengthUnit.Kilometer,
            center,
            LatLng(item.venue.lat, item.venue.lng),
          );
      return km <= radiusKm;
    }).toList();
  }

  Future<void> _showRouteToEvent(EventListItem item, LatLng mapCenter) async {
    if (_routeLoadingEventId != null) return;

    final from = ref.read(locationProvider).position ?? mapCenter;
    final to = LatLng(item.venue.lat, item.venue.lng);

    setState(() {
      _selectedEventId = item.event.id;
      _routeLoadingEventId = item.event.id;
    });

    try {
      final points = await _fetchRoutePoints(
        from: from,
        to: to,
        wheelchair: item.venue.isAccessible,
      );
      if (!mounted) return;
      setState(() {
        _routePoints = points;
        _routeEventId = item.event.id;
      });
      _fitRoute(points);
    } catch (_) {
      if (!mounted) return;
      _snack('Could not draw route, opening Google Maps');
      await _openGoogleDirections(to);
    } finally {
      if (mounted) setState(() => _routeLoadingEventId = null);
    }
  }

  Future<List<LatLng>> _fetchRoutePoints({
    required LatLng from,
    required LatLng to,
    required bool wheelchair,
  }) async {
    final apiKey = ApiConfig.orsApiKey.trim();
    if (apiKey.isEmpty) throw StateError('Missing ORS_API_KEY');

    final profile = wheelchair ? 'wheelchair' : 'foot-walking';
    final res = await Dio().post<Map<String, dynamic>>(
      'https://api.openrouteservice.org/v2/directions/$profile/geojson',
      options: Options(
        headers: {'Authorization': apiKey, 'Content-Type': 'application/json'},
      ),
      data: {
        'coordinates': [
          [from.longitude, from.latitude],
          [to.longitude, to.latitude],
        ],
      },
    );

    final coordinates =
        res.data?['features']?[0]?['geometry']?['coordinates'] as List?;
    if (coordinates == null || coordinates.isEmpty) {
      throw StateError('Empty route');
    }

    return coordinates.map((point) {
      final pair = point as List;
      return LatLng((pair[1] as num).toDouble(), (pair[0] as num).toDouble());
    }).toList();
  }

  void _fitRoute(List<LatLng> points) {
    if (points.isEmpty) return;
    if (points.length == 1) {
      _mapController.move(points.first, _focusedMapZoom);
      return;
    }
    _mapController.fitCamera(
      CameraFit.bounds(
        bounds: LatLngBounds.fromPoints(points),
        padding: const EdgeInsets.fromLTRB(48, 120, 48, 360),
      ),
    );
  }

  Future<void> _openGoogleDirections(LatLng destination) async {
    final uri = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=${destination.latitude},${destination.longitude}&travelmode=transit',
    );
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  void _snack(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  List<BusynessArea> _areasWithinRadius(
    List<BusynessArea> areas,
    LatLng? center,
    double radiusKm,
  ) {
    if (center == null) return areas;
    final distance = ll.Distance();
    return areas.where((area) {
      final km = distance.as(
        ll.LengthUnit.Kilometer,
        center,
        LatLng(area.lat, area.lng),
      );
      return km <= radiusKm;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final locationState = ref.watch(locationProvider);
    final eventsAsync = ref.watch(nearbyEventsProvider);
    final busynessAsync = ref.watch(busynessAreasProvider);
    final mapCenter = locationState.position ?? const LatLng(40.7580, -73.9855);
    final categoryFilters = _categoryFiltersFor(
      eventsAsync.valueOrNull ?? const [],
    );

    // Recenter on the user's location the first time it resolves — the map's
    // initialCenter is read before GPS returns, so without this it stays on the default.
    ref.listen(locationProvider, (prev, next) {
      if (!_mapCenteredOnLocation && next.position != null) {
        _mapCenteredOnLocation = true;
        _mapController.move(next.position!, _initialMapZoom);
      }
    });

    eventsAsync.whenData(
      (items) => _centerOnEventsIfNeeded(_upcomingEvents(items)),
    );

    return Scaffold(
      body: Stack(
        children: [
          // ── Map ──────────────────────────────────────────────────────────
          // Full-screen so the sheet floats over it; otherwise dragging the
          // sheet down reveals blank space below the map.
          Positioned.fill(
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: mapCenter,
                initialZoom: _initialMapZoom,
                onTap: (_, _) => setState(() => _selectedEventId = null),
                onPositionChanged: (camera, _) {
                  final nextZoom = camera.zoom;
                  if ((nextZoom - _currentZoom).abs() >= 0.05) {
                    setState(() => _currentZoom = nextZoom);
                  }
                },
                interactionOptions: const InteractionOptions(
                  flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
                ),
              ),
              children: [
                TileLayer(
                  urlTemplate:
                      'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                  subdomains: const ['a', 'b', 'c', 'd'],
                  maxZoom: 20,
                  userAgentPackageName: 'com.fromo.fromo',
                ),

                if (locationState.position != null)
                  CircleLayer(
                    circles: [
                      CircleMarker(
                        point: locationState.position!,
                        radius: _searchRadiusKm * 1000,
                        useRadiusInMeter: true,
                        color: FromoColors.teal.withValues(alpha: 0.08),
                        borderColor: FromoColors.teal.withValues(alpha: 0.35),
                        borderStrokeWidth: 2,
                      ),
                    ],
                  ),

                // User location dot
                if (locationState.position != null)
                  MarkerLayer(
                    markers: [_buildLocationDot(locationState.position!)],
                  ),

                if (_routePoints.length >= 2)
                  PolylineLayer(
                    polylines: [
                      Polyline(
                        points: _routePoints,
                        color: FromoColors.gray900.withValues(alpha: 0.88),
                        strokeWidth: 5,
                        borderColor: Colors.white,
                        borderStrokeWidth: 2,
                      ),
                    ],
                  ),

                // Event price pins
                eventsAsync.when(
                  data: (items) {
                    final scope = _buildMapScope(
                      items,
                      busynessAsync.valueOrNull ?? const [],
                      mapCenter,
                    );
                    return MarkerLayer(
                      markers: _buildEventMarkers(
                        scope.visibleItems,
                        scope.visibleAreas,
                        _currentZoom,
                      ).toList(),
                    );
                  },
                  loading: () => const MarkerLayer(markers: []),
                  error: (_, _) => const MarkerLayer(markers: []),
                ),
              ],
            ),
          ),

          // ── Top bar ──────────────────────────────────────────────────────
          SafeArea(
            child: _TopBar(
              onLocationTap: () {
                final pos = ref.read(locationProvider).position;
                if (pos != null) _mapController.move(pos, _initialMapZoom);
              },
            ),
          ),

          // ── Bottom draggable panel ────────────────────────────────────────
          DraggableScrollableSheet(
            initialChildSize: 0.45,
            minChildSize: 0.15,
            maxChildSize: 0.88,
            snap: true,
            snapSizes: const [0.15, 0.45, 0.88],
            builder: (context, scrollController) {
              return _BottomPanel(
                scrollController: scrollController,
                activeFilter: _activeFilter,
                categoryFilters: categoryFilters,
                onFilterChanged: (f) => setState(() => _activeFilter = f),
                showAllEvents: _showAllEvents,
                onScopeChanged: (showAll) =>
                    setState(() => _showAllEvents = showAll),
                accessibleOnly: _accessibleOnly,
                onAccessibleChanged: (value) =>
                    setState(() => _accessibleOnly = value),
                eventsAsync: eventsAsync,
                location: locationState.position,
                selectedEventId: _selectedEventId,
                routeEventId: _routeEventId,
                routeLoadingEventId: _routeLoadingEventId,
                applyFilter: _applyFilter,
                busynessAreas: busynessAsync.valueOrNull ?? const [],
                onDirections: (item) => _showRouteToEvent(item, mapCenter),
                onEventTap: (item) {
                  setState(() => _selectedEventId = item.event.id);
                  _mapController.move(
                    LatLng(item.venue.lat, item.venue.lng),
                    _focusedMapZoom,
                  );
                },
              );
            },
          ),

          // ── Loading spinner ───────────────────────────────────────────────
          if (locationState.isLoading)
            const Positioned(
              top: 100,
              left: 0,
              right: 0,
              child: Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }

  _MapScopeData _buildMapScope(
    List<EventListItem> items,
    List<BusynessArea> areas,
    LatLng center,
  ) {
    final categoryFilteredItems = _applyFilter(items);
    final scopedItems = _showAllEvents
        ? categoryFilteredItems
        : _eventsWithinRadius(categoryFilteredItems, center, _searchRadiusKm);
    final filteredItems = scopedItems.isEmpty
        ? categoryFilteredItems
        : scopedItems;
    final filteredAreas = _showAllEvents
        ? areas
        : _areasWithinRadius(areas, center, _searchRadiusKm);
    return _MapScopeData(
      visibleItems: filteredItems,
      visibleAreas: filteredAreas,
    );
  }

  List<String> _categoryFiltersFor(List<EventListItem> items) {
    final labelsByKey = <String, String>{};
    for (final item in _upcomingEvents(items)) {
      final rawCategory = _categoryForItem(item);
      final key = _categoryKey(rawCategory);
      if (key.isEmpty) continue;
      labelsByKey.putIfAbsent(key, () => _categoryLabel(rawCategory!));
    }

    final labels = labelsByKey.values.toList()
      ..sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));
    return [_allCategoryFilter, ...labels];
  }

  _CrowdBadgeData _crowdForEvent(EventListItem item, List<BusynessArea> areas) {
    final area = _matchingAreaForEvent(item, areas);
    return _crowdVisualForArea(area);
  }

  BusynessArea? _matchingAreaForEvent(
    EventListItem item,
    List<BusynessArea> areas,
  ) {
    if (areas.isEmpty) return null;

    final distance = ll.Distance();
    BusynessArea? closest;
    double closestMeters = double.infinity;

    for (final area in areas) {
      final meters = distance.as(
        ll.LengthUnit.Meter,
        LatLng(item.venue.lat, item.venue.lng),
        LatLng(area.lat, area.lng),
      );
      if (meters <= area.radiusMetres) return area;
      if (meters < closestMeters) {
        closestMeters = meters;
        closest = area;
      }
    }

    return closestMeters <= 400 ? closest : null;
  }

  _CrowdBadgeData _crowdVisualForArea(BusynessArea? area) {
    final level = area?.level;
    final score = area?.score;

    if (level == 'busy' || (score != null && score >= 0.67)) {
      return const _CrowdBadgeData(
        label: 'High crowd',
        color: Color(0xFFEF4444),
        glowColor: Color(0xFFFCA5A5),
      );
    }

    if (level == 'quiet' || (score != null && score <= 0.33)) {
      return const _CrowdBadgeData(
        label: 'Low crowd',
        color: Color(0xFF22C55E),
        glowColor: Color(0xFF86EFAC),
      );
    }

    return const _CrowdBadgeData(
      label: 'Medium crowd',
      color: Color(0xFFF59E0B),
      glowColor: Color(0xFFFDE68A),
    );
  }

  List<Marker> _buildEventMarkers(
    List<EventListItem> items,
    List<BusynessArea> areas,
    double zoom,
  ) {
    final clusters = _clusterEvents(items, zoom);
    if (zoom < _singleEventZoom) {
      return clusters.map((cluster) {
        if (cluster.isSingle) {
          final item = cluster.items.first;
          return _buildEventPin(
            item,
            _crowdForEvent(item, areas),
            offset: Offset.zero,
            siblingCount: 1,
            isAccessible: item.venue.isAccessible,
          );
        }
        return _buildClusterPin(cluster, areas, zoom);
      }).toList();
    }

    final buckets = <String, List<EventListItem>>{};
    for (final item in items) {
      final key =
          '${item.venue.lat.toStringAsFixed(3)},${item.venue.lng.toStringAsFixed(3)}';
      buckets.putIfAbsent(key, () => []).add(item);
    }

    final layouts = <_PinLayout>[];
    for (final bucket in buckets.values) {
      if (bucket.length == 1) {
        layouts.add(
          _PinLayout(item: bucket.first, offset: Offset.zero, siblingCount: 1),
        );
        continue;
      }

      final radius = bucket.length == 2 ? 18.0 : 24.0;
      for (var i = 0; i < bucket.length; i++) {
        final angle = (-math.pi / 2) + ((2 * math.pi * i) / bucket.length);
        layouts.add(
          _PinLayout(
            item: bucket[i],
            offset: Offset(math.cos(angle) * radius, math.sin(angle) * radius),
            siblingCount: bucket.length,
          ),
        );
      }
    }

    return layouts
        .map(
          (layout) => _buildEventPin(
            layout.item,
            _crowdForEvent(layout.item, areas),
            offset: layout.offset,
            siblingCount: layout.siblingCount,
            isAccessible: layout.item.venue.isAccessible,
          ),
        )
        .toList();
  }

  List<_EventCluster> _clusterEvents(List<EventListItem> items, double zoom) {
    if (items.isEmpty) return const [];
    if (zoom >= _singleEventZoom) {
      return items
          .map(
            (item) => _EventCluster(
              center: LatLng(item.venue.lat, item.venue.lng),
              items: [item],
            ),
          )
          .toList();
    }

    final radiusMeters = zoom < _midClusterZoom ? 520.0 : 180.0;
    final distance = ll.Distance();
    final clusters = <_EventCluster>[];

    for (final item in items) {
      final point = LatLng(item.venue.lat, item.venue.lng);
      var matchedIndex = -1;
      var matchedDistance = double.infinity;

      for (var i = 0; i < clusters.length; i++) {
        final meters = distance.as(
          ll.LengthUnit.Meter,
          point,
          clusters[i].center,
        );
        if (meters <= radiusMeters && meters < matchedDistance) {
          matchedIndex = i;
          matchedDistance = meters;
        }
      }

      if (matchedIndex == -1) {
        clusters.add(_EventCluster(center: point, items: [item]));
        continue;
      }

      final matched = clusters[matchedIndex];
      final nextItems = [...matched.items, item];
      clusters[matchedIndex] = _EventCluster(
        center: _clusterCenter(nextItems),
        items: nextItems,
      );
    }

    return clusters;
  }

  LatLng _clusterCenter(List<EventListItem> items) {
    final lat =
        items.map((item) => item.venue.lat).reduce((a, b) => a + b) /
        items.length;
    final lng =
        items.map((item) => item.venue.lng).reduce((a, b) => a + b) /
        items.length;
    return LatLng(lat, lng);
  }

  Marker _buildLocationDot(LatLng pos) {
    return Marker(
      point: pos,
      width: 20,
      height: 20,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.blue,
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white, width: 3),
          boxShadow: [
            BoxShadow(
              color: Colors.blue.withValues(alpha: 0.35),
              blurRadius: 8,
              spreadRadius: 2,
            ),
          ],
        ),
      ),
    );
  }

  Marker _buildEventPin(
    EventListItem item,
    _CrowdBadgeData crowd, {
    required Offset offset,
    required int siblingCount,
    required bool isAccessible,
  }) {
    final isSelected = _selectedEventId == item.event.id;
    return Marker(
      point: LatLng(item.venue.lat, item.venue.lng),
      width: 124,
      height: 110,
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedEventId = item.event.id);
          _mapController.move(
            LatLng(item.venue.lat, item.venue.lng),
            _focusedMapZoom,
          );
          context.push('/events/${item.event.id}');
        },
        child: Transform.translate(
          offset: offset,
          child: _PulseEventPin(
            isSelected: isSelected,
            priceLabel: item.event.priceDisplay,
            crowd: crowd,
            siblingCount: siblingCount,
            isAccessible: isAccessible,
          ),
        ),
      ),
    );
  }

  Marker _buildClusterPin(
    _EventCluster cluster,
    List<BusynessArea> areas,
    double zoom,
  ) {
    final crowd = _crowdForCluster(cluster, areas);
    final count = cluster.items.length;
    final size = count >= 8
        ? 86.0
        : count >= 4
        ? 76.0
        : 66.0;
    return Marker(
      point: cluster.center,
      width: size + 30,
      height: size + 30,
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedEventId = null);
          _mapController.move(
            cluster.center,
            math.min(zoom + 1.6, _focusedMapZoom),
          );
        },
        child: _ClusterEventPin(
          count: count,
          crowd: crowd,
          size: size,
          hasAccessible: cluster.items.any((item) => item.venue.isAccessible),
        ),
      ),
    );
  }

  _CrowdBadgeData _crowdForCluster(
    _EventCluster cluster,
    List<BusynessArea> areas,
  ) {
    final crowds = cluster.items.map((item) => _crowdForEvent(item, areas));
    return crowds.reduce((current, next) {
      final currentRank = _crowdRank(current);
      final nextRank = _crowdRank(next);
      return nextRank > currentRank ? next : current;
    });
  }

  int _crowdRank(_CrowdBadgeData crowd) {
    if (crowd.label == 'High crowd') return 3;
    if (crowd.label == 'Medium crowd') return 2;
    return 1;
  }
}

// ── Top bar ────────────────────────────────────────────────────────────────────

class _TopBar extends ConsumerWidget {
  final VoidCallback onLocationTap;
  const _TopBar({required this.onLocationTap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cityName = ref.watch(cityNameProvider).valueOrNull ?? 'Locating…';
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Material(
        elevation: 2,
        borderRadius: BorderRadius.circular(12),
        color: Colors.white,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onLocationTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            child: Row(
              children: [
                const Icon(
                  Icons.location_on,
                  color: FromoColors.teal,
                  size: 18,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    cityName,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      color: FromoColors.gray900,
                      fontSize: 15,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                // Tapping the bar recenters on the user; this icon hints at that.
                const Icon(
                  Icons.my_location,
                  color: FromoColors.gray500,
                  size: 18,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ── Bottom panel ───────────────────────────────────────────────────────────────

class _BottomPanel extends StatelessWidget {
  final ScrollController scrollController;
  final String activeFilter;
  final List<String> categoryFilters;
  final ValueChanged<String> onFilterChanged;
  final bool showAllEvents;
  final ValueChanged<bool> onScopeChanged;
  final bool accessibleOnly;
  final ValueChanged<bool> onAccessibleChanged;
  final AsyncValue<List<EventListItem>> eventsAsync;
  final LatLng? location;
  final String? selectedEventId;
  final String? routeEventId;
  final String? routeLoadingEventId;
  final List<EventListItem> Function(List<EventListItem>) applyFilter;
  final List<BusynessArea> busynessAreas;
  final ValueChanged<EventListItem> onDirections;
  final ValueChanged<EventListItem> onEventTap;

  const _BottomPanel({
    required this.scrollController,
    required this.activeFilter,
    required this.categoryFilters,
    required this.onFilterChanged,
    required this.showAllEvents,
    required this.onScopeChanged,
    required this.accessibleOnly,
    required this.onAccessibleChanged,
    required this.eventsAsync,
    required this.location,
    required this.selectedEventId,
    required this.routeEventId,
    required this.routeLoadingEventId,
    required this.applyFilter,
    required this.busynessAreas,
    required this.onDirections,
    required this.onEventTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: FromoColors.gray50,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 12,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: CustomScrollView(
        controller: scrollController,
        slivers: [
          // Drag handle
          SliverToBoxAdapter(
            child: Center(
              child: Padding(
                padding: const EdgeInsets.only(top: 10, bottom: 6),
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: FromoColors.gray200,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
            ),
          ),

          // Filter chips
          SliverToBoxAdapter(
            child: Container(
              color: Colors.white,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                    child: Row(
                      children: [
                        _ScopeChip(
                          label: 'Nearby',
                          isActive: !showAllEvents,
                          onTap: () => onScopeChanged(false),
                        ),
                        const SizedBox(width: 8),
                        _ScopeChip(
                          label: 'All events',
                          isActive: showAllEvents,
                          onTap: () => onScopeChanged(true),
                        ),
                        const SizedBox(width: 8),
                        _ScopeChip(
                          label: 'Accessible',
                          icon: Icons.accessible_forward,
                          isActive: accessibleOnly,
                          onTap: () => onAccessibleChanged(!accessibleOnly),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(
                    height: 48,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      itemCount: categoryFilters.length,
                      separatorBuilder: (_, _) => const SizedBox(width: 8),
                      itemBuilder: (_, i) {
                        final cat = categoryFilters[i];
                        final isActive =
                            _categoryKey(activeFilter) == _categoryKey(cat);
                        return GestureDetector(
                          onTap: () => onFilterChanged(cat),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 150),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: isActive
                                  ? FromoColors.teal
                                  : FromoColors.gray100,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              cat,
                              style: TextStyle(
                                color: isActive
                                    ? Colors.white
                                    : FromoColors.gray700,
                                fontWeight: FontWeight.w500,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                    child: Text(
                      showAllEvents
                          ? 'Showing all loaded events'
                          : location == null
                          ? 'Showing currently loaded events'
                          : _eventsWithinRadius(
                              applyFilter(
                                eventsAsync.valueOrNull ??
                                    const <EventListItem>[],
                              ),
                              location,
                              _searchRadiusKm,
                            ).isEmpty
                          ? 'No events within ${_searchRadiusKm.toStringAsFixed(0)} km, showing all loaded events'
                          : 'Showing events within ${_searchRadiusKm.toStringAsFixed(0)} km of you',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: FromoColors.gray500,
                      ),
                    ),
                  ),
                  if (const bool.fromEnvironment('USE_DEMO_LOCATION'))
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                      child: eventsAsync.when(
                        data: (items) {
                          final filteredCount = applyFilter(items).length;
                          return Text(
                            'Demo debug: loaded ${items.length}, visible $filteredCount',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: FromoColors.gray500,
                            ),
                          );
                        },
                        loading: () => const Text(
                          'Demo debug: loading events...',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: FromoColors.gray500,
                          ),
                        ),
                        error: (error, _) => Text(
                          'Demo debug: events error $error',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: FromoColors.gray500,
                          ),
                        ),
                      ),
                    ),
                  Divider(height: 1, color: FromoColors.gray200),
                ],
              ),
            ),
          ),

          // Activity list
          eventsAsync.when(
            data: (items) {
              final categoryFilteredItems = applyFilter(items);
              final scopedItems = _eventsWithinRadius(
                categoryFilteredItems,
                location,
                _searchRadiusKm,
              );
              final filtered = showAllEvents
                  ? categoryFilteredItems
                  : scopedItems.isEmpty
                  ? categoryFilteredItems
                  : scopedItems;
              final visibleAreas = showAllEvents
                  ? busynessAreas
                  : _areasWithinRadius(
                      busynessAreas,
                      location,
                      _searchRadiusKm,
                    );
              if (filtered.isEmpty) {
                return const SliverFillRemaining(
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.search_off,
                          size: 48,
                          color: FromoColors.gray200,
                        ),
                        SizedBox(height: 12),
                        Text(
                          'No events nearby',
                          style: TextStyle(color: FromoColors.gray500),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Try adjusting your filters',
                          style: TextStyle(
                            color: FromoColors.gray500,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }
              return SliverPadding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                sliver: SliverList.separated(
                  itemCount: filtered.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, i) => _ActivityCard(
                    item: filtered[i],
                    isSelected: selectedEventId == filtered[i].event.id,
                    routeActive: routeEventId == filtered[i].event.id,
                    routeLoading: routeLoadingEventId == filtered[i].event.id,
                    crowd: _crowdForEvent(filtered[i], visibleAreas),
                    onTap: () {
                      onEventTap(filtered[i]);
                      context.push('/events/${filtered[i].event.id}');
                    },
                    onDirections: () => onDirections(filtered[i]),
                  ),
                ),
              );
            },
            loading: () => const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (_, _) => const SliverFillRemaining(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.search_off,
                      size: 48,
                      color: FromoColors.gray200,
                    ),
                    SizedBox(height: 12),
                    Text(
                      'No events nearby',
                      style: TextStyle(color: FromoColors.gray500),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Please try again in a moment',
                      style: TextStyle(
                        color: FromoColors.gray500,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

List<EventListItem> _eventsWithinRadius(
  List<EventListItem> items,
  LatLng? center,
  double radiusKm,
) {
  if (center == null) return items;
  final distance = ll.Distance();
  return items.where((item) {
    final km =
        item.distanceKm ??
        distance.as(
          ll.LengthUnit.Kilometer,
          center,
          LatLng(item.venue.lat, item.venue.lng),
        );
    return km <= radiusKm;
  }).toList();
}

List<BusynessArea> _areasWithinRadius(
  List<BusynessArea> areas,
  LatLng? center,
  double radiusKm,
) {
  if (center == null) return areas;
  final distance = ll.Distance();
  return areas.where((area) {
    final km = distance.as(
      ll.LengthUnit.Kilometer,
      center,
      LatLng(area.lat, area.lng),
    );
    return km <= radiusKm;
  }).toList();
}

_CrowdBadgeData _crowdForEvent(EventListItem item, List<BusynessArea> areas) {
  final area = _matchingAreaForEvent(item, areas);
  return _crowdVisualForArea(area);
}

BusynessArea? _matchingAreaForEvent(
  EventListItem item,
  List<BusynessArea> areas,
) {
  if (areas.isEmpty) return null;

  final distance = ll.Distance();
  BusynessArea? closest;
  double closestMeters = double.infinity;

  for (final area in areas) {
    final meters = distance.as(
      ll.LengthUnit.Meter,
      LatLng(item.venue.lat, item.venue.lng),
      LatLng(area.lat, area.lng),
    );
    if (meters <= area.radiusMetres) return area;
    if (meters < closestMeters) {
      closestMeters = meters;
      closest = area;
    }
  }

  return closestMeters <= 400 ? closest : null;
}

_CrowdBadgeData _crowdVisualForArea(BusynessArea? area) {
  final level = area?.level;
  final score = area?.score;

  if (level == 'busy' || (score != null && score >= 0.67)) {
    return const _CrowdBadgeData(
      label: 'High crowd',
      color: Color(0xFFEF4444),
      glowColor: Color(0xFFFCA5A5),
    );
  }

  if (level == 'quiet' || (score != null && score <= 0.33)) {
    return const _CrowdBadgeData(
      label: 'Low crowd',
      color: Color(0xFF22C55E),
      glowColor: Color(0xFF86EFAC),
    );
  }

  return const _CrowdBadgeData(
    label: 'Medium crowd',
    color: Color(0xFFF59E0B),
    glowColor: Color(0xFFFDE68A),
  );
}

// ── Activity card ──────────────────────────────────────────────────────────────

class _ActivityCard extends StatelessWidget {
  final EventListItem item;
  final bool isSelected;
  final bool routeActive;
  final bool routeLoading;
  final _CrowdBadgeData crowd;
  final VoidCallback onTap;
  final VoidCallback onDirections;

  const _ActivityCard({
    required this.item,
    required this.isSelected,
    required this.routeActive,
    required this.routeLoading,
    required this.crowd,
    required this.onTap,
    required this.onDirections,
  });

  @override
  Widget build(BuildContext context) {
    final event = item.event;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? FromoColors.teal : Colors.transparent,
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: _ActivityThumbnail(imageUrl: event.imageUrl),
            ),
            const SizedBox(width: 12),

            // Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title
                  Text(
                    event.title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                      color: FromoColors.gray900,
                      height: 1.3,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),

                  const SizedBox(height: 6),

                  _CrowdChip(crowd: crowd),

                  if (item.venue.isAccessible) ...[
                    const SizedBox(height: 5),
                    const _AccessibleBadge(),
                  ],

                  const SizedBox(height: 3),

                  // Venue + description
                  Text(
                    event.description != null && event.description!.isNotEmpty
                        ? event.description!
                        : item.venue.name,
                    style: const TextStyle(
                      fontSize: 12,
                      color: FromoColors.gray500,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),

                  const SizedBox(height: 6),

                  // Distance + time
                  Row(
                    children: [
                      const Icon(
                        Icons.location_on_outlined,
                        size: 12,
                        color: FromoColors.gray500,
                      ),
                      const SizedBox(width: 2),
                      Text(
                        item.distanceKm != null
                            ? '${item.distanceKm!.toStringAsFixed(1)} km'
                            : 'Nearby',
                        style: const TextStyle(
                          fontSize: 11,
                          color: FromoColors.gray500,
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Icon(
                        Icons.access_time,
                        size: 12,
                        color: FromoColors.gray500,
                      ),
                      const SizedBox(width: 2),
                      Expanded(
                        child: Text(
                          _formatTime(event.startsAt),
                          style: const TextStyle(
                            fontSize: 11,
                            color: FromoColors.gray500,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 6),

                  // Price row + badges
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Strikethrough original price
                      if (event.isLastMinuteDeal) ...[
                        Text(
                          event.originalPriceDisplay!,
                          style: const TextStyle(
                            fontSize: 12,
                            color: FromoColors.gray500,
                            decoration: TextDecoration.lineThrough,
                          ),
                        ),
                        const SizedBox(width: 4),
                      ],

                      // Current price
                      Text(
                        event.priceDisplay,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: event.isFree
                              ? FromoColors.gray900
                              : FromoColors.green600,
                        ),
                      ),

                      const SizedBox(width: 6),

                      // Last-minute deal badge
                      if (event.isLastMinuteDeal)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 7,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFFF3CD),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Text(
                            'Last-minute deal',
                            style: TextStyle(
                              fontSize: 10,
                              color: Color(0xFF856404),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        )
                      // Spots left badge (when no deal badge)
                      else if (event.spotsRemaining != null &&
                          event.spotsRemaining! <= 10)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 7,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFFF3CD),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            '${event.spotsRemaining} spots left',
                            style: const TextStyle(
                              fontSize: 10,
                              color: Color(0xFF856404),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),

                      const Spacer(),

                      // Get Directions button
                      GestureDetector(
                        onTap: routeLoading ? null : onDirections,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: routeActive
                                ? FromoColors.teal
                                : FromoColors.teal.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (routeLoading)
                                SizedBox(
                                  width: 13,
                                  height: 13,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: routeActive
                                        ? Colors.white
                                        : FromoColors.teal,
                                  ),
                                )
                              else
                                Icon(
                                  Icons.alt_route,
                                  size: 13,
                                  color: routeActive
                                      ? Colors.white
                                      : FromoColors.teal,
                                ),
                              const SizedBox(width: 3),
                              Text(
                                routeActive ? 'Route' : 'Directions',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: routeActive
                                      ? Colors.white
                                      : FromoColors.teal,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final now = DateTime.now();
    final diff = dt.difference(now);
    if (diff.inDays == 0) return 'Today ${_hm(dt)}';
    if (diff.inDays == 1) return 'Tomorrow ${_hm(dt)}';
    return '${_weekday(dt)} ${_hm(dt)}';
  }

  String _hm(DateTime dt) {
    final h = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
    final m = dt.minute.toString().padLeft(2, '0');
    final period = dt.hour < 12 ? 'AM' : 'PM';
    return '$h:$m $period';
  }

  String _weekday(DateTime dt) {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days[dt.weekday - 1];
  }
}

class _ActivityThumbnail extends StatelessWidget {
  final String? imageUrl;

  const _ActivityThumbnail({required this.imageUrl});

  @override
  Widget build(BuildContext context) {
    final normalizedUrl = imageUrl?.trim();
    if (normalizedUrl == null || normalizedUrl.isEmpty) {
      return const _ActivityThumbnailPlaceholder();
    }

    return CachedNetworkImage(
      imageUrl: normalizedUrl,
      width: 80,
      height: 80,
      fit: BoxFit.cover,
      placeholder: (_, _) => const _ActivityThumbnailPlaceholder(),
      errorWidget: (_, _, _) => const _ActivityThumbnailPlaceholder(),
    );
  }
}

class _ActivityThumbnailPlaceholder extends StatelessWidget {
  const _ActivityThumbnailPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 80,
      height: 80,
      color: FromoColors.gray100,
      child: const Icon(Icons.event, color: FromoColors.gray500, size: 32),
    );
  }
}

class _ScopeChip extends StatelessWidget {
  final String label;
  final IconData? icon;
  final bool isActive;
  final VoidCallback onTap;

  const _ScopeChip({
    required this.label,
    this.icon,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: isActive ? FromoColors.teal : FromoColors.gray100,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(
                icon,
                size: 15,
                color: isActive ? Colors.white : FromoColors.gray700,
              ),
              const SizedBox(width: 5),
            ],
            Text(
              label,
              style: TextStyle(
                color: isActive ? Colors.white : FromoColors.gray700,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CrowdChip extends StatelessWidget {
  final _CrowdBadgeData crowd;
  const _CrowdChip({required this.crowd});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: crowd.color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        crowd.label,
        style: TextStyle(
          color: crowd.color,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _AccessibleBadge extends StatelessWidget {
  const _AccessibleBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: FromoColors.teal.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: FromoColors.teal.withValues(alpha: 0.18)),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.accessible_forward, size: 13, color: FromoColors.teal),
          SizedBox(width: 4),
          Text(
            'Step-free',
            style: TextStyle(
              color: FromoColors.teal,
              fontSize: 10,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _ClusterEventPin extends StatelessWidget {
  final int count;
  final _CrowdBadgeData crowd;
  final double size;
  final bool hasAccessible;

  const _ClusterEventPin({
    required this.count,
    required this.crowd,
    required this.size,
    required this.hasAccessible,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: size + 26,
          height: size + 26,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: crowd.glowColor.withValues(alpha: 0.22),
          ),
        ),
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: crowd.color,
            border: Border.all(color: Colors.white, width: 3),
            boxShadow: [
              BoxShadow(
                color: crowd.color.withValues(alpha: 0.30),
                blurRadius: 14,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '$count',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                  height: 1,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                count == 1 ? 'event' : 'events',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  height: 1,
                ),
              ),
            ],
          ),
        ),
        if (hasAccessible)
          Positioned(
            right: 6,
            bottom: 6,
            child: Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                border: Border.all(color: FromoColors.teal, width: 2),
              ),
              child: const Icon(
                Icons.accessible_forward,
                size: 15,
                color: FromoColors.teal,
              ),
            ),
          ),
      ],
    );
  }
}

class _PulseEventPin extends StatefulWidget {
  final bool isSelected;
  final String priceLabel;
  final _CrowdBadgeData crowd;
  final int siblingCount;
  final bool isAccessible;

  const _PulseEventPin({
    required this.isSelected,
    required this.priceLabel,
    required this.crowd,
    required this.siblingCount,
    required this.isAccessible,
  });

  @override
  State<_PulseEventPin> createState() => _PulseEventPinState();
}

class _PulseEventPinState extends State<_PulseEventPin>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1800),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final t = _controller.value;
        final haloScale = 0.92 + (t * 0.22);
        final haloAlpha = 0.10 + ((1 - t) * 0.18);

        return Stack(
          alignment: Alignment.center,
          children: [
            Transform.scale(
              scale: haloScale,
              child: Container(
                width: widget.isSelected ? 84 : 74,
                height: widget.isSelected ? 84 : 74,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: widget.crowd.glowColor.withValues(alpha: haloAlpha),
                ),
              ),
            ),
            AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: widget.isSelected
                    ? FromoColors.tealDark
                    : FromoColors.teal,
                borderRadius: BorderRadius.circular(999),
                border: widget.isSelected
                    ? Border.all(color: Colors.white, width: 2)
                    : null,
                boxShadow: [
                  BoxShadow(
                    color: widget.crowd.color.withValues(alpha: 0.28),
                    blurRadius: widget.isSelected ? 14 : 8,
                    spreadRadius: widget.isSelected ? 1.5 : 0.5,
                  ),
                ],
              ),
              child: Text(
                widget.priceLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (widget.siblingCount > 1)
              Positioned(
                top: 16,
                right: 18,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 5,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(
                      color: widget.crowd.color.withValues(alpha: 0.35),
                    ),
                  ),
                  child: Text(
                    '${widget.siblingCount}',
                    style: TextStyle(
                      color: widget.crowd.color,
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
            if (widget.isAccessible)
              Positioned(
                left: 18,
                bottom: 16,
                child: Container(
                  width: 23,
                  height: 23,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    border: Border.all(color: FromoColors.teal, width: 2),
                  ),
                  child: const Icon(
                    Icons.accessible_forward,
                    size: 14,
                    color: FromoColors.teal,
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
