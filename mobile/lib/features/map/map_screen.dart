import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';
import 'package:latlong2/latlong.dart' as ll;
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme.dart';
import '../../shared/models/event.dart';
import 'map_providers.dart';

const _filterCategories = ['All', 'Food', 'Music', 'Sports', 'Nightlife', 'Outdoors', 'Study'];

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

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  final _mapController = MapController();
  String? _selectedEventId;
  String _activeFilter = 'All';
  bool _mapCenteredOnEvents = false;
  bool _mapCenteredOnLocation = false;

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
    _mapController.move(center, 13);
  }

  @override
  void dispose() {
    _mapController.dispose();
    super.dispose();
  }

  List<EventListItem> _applyFilter(List<EventListItem> items) {
    if (_activeFilter == 'All') return items;
    return items.where((i) =>
        (i.event.category ?? '').toLowerCase() == _activeFilter.toLowerCase()).toList();
  }

  @override
  Widget build(BuildContext context) {
    final locationState = ref.watch(locationProvider);
    final eventsAsync = ref.watch(nearbyEventsProvider);
    final busynessAsync = ref.watch(busynessAreasProvider);

    // Recenter on the user's location the first time it resolves — the map's
    // initialCenter is read before GPS returns, so without this it stays on the default.
    ref.listen(locationProvider, (prev, next) {
      if (!_mapCenteredOnLocation && next.position != null) {
        _mapCenteredOnLocation = true;
        _mapController.move(next.position!, 14);
      }
    });

    eventsAsync.whenData(_centerOnEventsIfNeeded);

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
                initialCenter: locationState.position ?? const LatLng(40.7580, -73.9855),
                initialZoom: 14,
                onTap: (_, _) => setState(() => _selectedEventId = null),
                interactionOptions: const InteractionOptions(
                  flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
                ),
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                  subdomains: const ['a', 'b', 'c', 'd'],
                  userAgentPackageName: 'com.fromo.fromo',
                ),

                // User location dot
                if (locationState.position != null)
                  MarkerLayer(markers: [_buildLocationDot(locationState.position!)]),

                // Event price pins
                eventsAsync.when(
                  data: (items) => MarkerLayer(
                    markers: _buildEventMarkers(
                      _applyFilter(items),
                      busynessAsync.valueOrNull ?? const [],
                    )
                        .toList(),
                  ),
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
                if (pos != null) _mapController.move(pos, 14);
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
                onFilterChanged: (f) => setState(() => _activeFilter = f),
                eventsAsync: eventsAsync,
                selectedEventId: _selectedEventId,
                applyFilter: _applyFilter,
                busynessAreas: busynessAsync.valueOrNull ?? const [],
                onEventTap: (item) {
                  setState(() => _selectedEventId = item.event.id);
                  _mapController.move(LatLng(item.venue.lat, item.venue.lng), 15);
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

  _CrowdBadgeData _crowdForEvent(EventListItem item, List<BusynessArea> areas) {
    if (areas.isEmpty) {
      return const _CrowdBadgeData(
        label: 'Medium crowd',
        color: Color(0xFFF59E0B),
        glowColor: Color(0xFFFDE68A),
      );
    }

    final distance = ll.Distance();
    BusynessArea? closest;
    double closestMeters = double.infinity;

    for (final area in areas) {
      final meters = distance.as(
        ll.LengthUnit.Meter,
        LatLng(item.venue.lat, item.venue.lng),
        LatLng(area.lat, area.lng),
      );
      if (meters < closestMeters) {
        closestMeters = meters;
        closest = area;
      }
    }

    switch (closest?.level) {
      case 'busy':
        return const _CrowdBadgeData(
          label: 'High crowd',
          color: Color(0xFFEF4444),
          glowColor: Color(0xFFFCA5A5),
        );
      case 'quiet':
        return const _CrowdBadgeData(
          label: 'Low crowd',
          color: Color(0xFF22C55E),
          glowColor: Color(0xFF86EFAC),
        );
      default:
        return const _CrowdBadgeData(
          label: 'Medium crowd',
          color: Color(0xFFF59E0B),
          glowColor: Color(0xFFFDE68A),
        );
    }
  }

  List<Marker> _buildEventMarkers(
    List<EventListItem> items,
    List<BusynessArea> areas,
  ) {
    final buckets = <String, List<EventListItem>>{};
    for (final item in items) {
      final key =
          '${item.venue.lat.toStringAsFixed(3)},${item.venue.lng.toStringAsFixed(3)}';
      buckets.putIfAbsent(key, () => []).add(item);
    }

    final layouts = <_PinLayout>[];
    for (final bucket in buckets.values) {
      if (bucket.length == 1) {
        layouts.add(_PinLayout(
          item: bucket.first,
          offset: Offset.zero,
          siblingCount: 1,
        ));
        continue;
      }

      final radius = bucket.length == 2 ? 18.0 : 24.0;
      for (var i = 0; i < bucket.length; i++) {
        final angle = (-math.pi / 2) + ((2 * math.pi * i) / bucket.length);
        layouts.add(_PinLayout(
          item: bucket[i],
          offset: Offset(
            math.cos(angle) * radius,
            math.sin(angle) * radius,
          ),
          siblingCount: bucket.length,
        ));
      }
    }

    return layouts
        .map((layout) => _buildEventPin(
              layout.item,
              _crowdForEvent(layout.item, areas),
              offset: layout.offset,
              siblingCount: layout.siblingCount,
            ))
        .toList();
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
  }) {
    final isSelected = _selectedEventId == item.event.id;
    return Marker(
      point: LatLng(item.venue.lat, item.venue.lng),
      width: 124,
      height: 110,
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedEventId = item.event.id);
          _mapController.move(LatLng(item.venue.lat, item.venue.lng), 15);
        },
        child: Transform.translate(
          offset: offset,
          child: _PulseEventPin(
            isSelected: isSelected,
            priceLabel: item.event.priceDisplay,
            crowd: crowd,
            siblingCount: siblingCount,
          ),
        ),
      ),
    );
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
                const Icon(Icons.location_on, color: FromoColors.teal, size: 18),
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
                const Icon(Icons.my_location, color: FromoColors.gray500, size: 18),
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
  final ValueChanged<String> onFilterChanged;
  final AsyncValue<List<EventListItem>> eventsAsync;
  final String? selectedEventId;
  final List<EventListItem> Function(List<EventListItem>) applyFilter;
  final List<BusynessArea> busynessAreas;
  final ValueChanged<EventListItem> onEventTap;

  const _BottomPanel({
    required this.scrollController,
    required this.activeFilter,
    required this.onFilterChanged,
    required this.eventsAsync,
    required this.selectedEventId,
    required this.applyFilter,
    required this.busynessAreas,
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
                  SizedBox(
                    height: 48,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      itemCount: _filterCategories.length,
                      separatorBuilder: (_, _) => const SizedBox(width: 8),
                      itemBuilder: (_, i) {
                        final cat = _filterCategories[i];
                        final isActive = activeFilter == cat;
                        return GestureDetector(
                          onTap: () => onFilterChanged(cat),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 150),
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                            decoration: BoxDecoration(
                              color: isActive ? FromoColors.teal : FromoColors.gray100,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              cat,
                              style: TextStyle(
                                color: isActive ? Colors.white : FromoColors.gray700,
                                fontWeight: FontWeight.w500,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        );
                      },
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
              final filtered = applyFilter(items);
              if (filtered.isEmpty) {
                return const SliverFillRemaining(
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.search_off, size: 48, color: FromoColors.gray200),
                        SizedBox(height: 12),
                        Text('No events nearby', style: TextStyle(color: FromoColors.gray500)),
                        SizedBox(height: 4),
                        Text('Try adjusting your filters',
                            style: TextStyle(color: FromoColors.gray500, fontSize: 12)),
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
                    crowd: _crowdForEvent(filtered[i], busynessAreas),
                    onTap: () {
                      onEventTap(filtered[i]);
                      context.push('/events/${filtered[i].event.id}');
                    },
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
                    Icon(Icons.search_off, size: 48, color: FromoColors.gray200),
                    SizedBox(height: 12),
                    Text('No events nearby', style: TextStyle(color: FromoColors.gray500)),
                    SizedBox(height: 4),
                    Text(
                      'Please try again in a moment',
                      style: TextStyle(color: FromoColors.gray500, fontSize: 12),
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

_CrowdBadgeData _crowdForEvent(EventListItem item, List<BusynessArea> areas) {
  if (areas.isEmpty) {
    return const _CrowdBadgeData(
      label: 'Medium crowd',
      color: Color(0xFFF59E0B),
      glowColor: Color(0xFFFDE68A),
    );
  }

  final distance = ll.Distance();
  BusynessArea? closest;
  double closestMeters = double.infinity;

  for (final area in areas) {
    final meters = distance.as(
      ll.LengthUnit.Meter,
      LatLng(item.venue.lat, item.venue.lng),
      LatLng(area.lat, area.lng),
    );
    if (meters < closestMeters) {
      closestMeters = meters;
      closest = area;
    }
  }

  switch (closest?.level) {
    case 'busy':
      return const _CrowdBadgeData(
        label: 'High crowd',
        color: Color(0xFFEF4444),
        glowColor: Color(0xFFFCA5A5),
      );
    case 'quiet':
      return const _CrowdBadgeData(
        label: 'Low crowd',
        color: Color(0xFF22C55E),
        glowColor: Color(0xFF86EFAC),
      );
    default:
      return const _CrowdBadgeData(
        label: 'Medium crowd',
        color: Color(0xFFF59E0B),
        glowColor: Color(0xFFFDE68A),
      );
  }
}

// ── Activity card ──────────────────────────────────────────────────────────────

class _ActivityCard extends StatelessWidget {
  final EventListItem item;
  final bool isSelected;
  final _CrowdBadgeData crowd;
  final VoidCallback onTap;

  const _ActivityCard({
    required this.item,
    required this.isSelected,
    required this.crowd,
    required this.onTap,
  });

  Future<void> _openDirections() async {
    final lat = item.venue.lat;
    final lng = item.venue.lng;
    final uri = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=$lat,$lng&travelmode=transit',
    );
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

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
            // Image placeholder
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Container(
                width: 80,
                height: 80,
                color: FromoColors.gray100,
                child: const Icon(Icons.event, color: FromoColors.gray500, size: 32),
              ),
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

                  const SizedBox(height: 3),

                  // Venue + description
                  Text(
                    event.description != null && event.description!.isNotEmpty
                        ? event.description!
                        : item.venue.name,
                    style: const TextStyle(fontSize: 12, color: FromoColors.gray500),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),

                  const SizedBox(height: 6),

                  // Distance + time
                  Row(
                    children: [
                      const Icon(Icons.location_on_outlined, size: 12, color: FromoColors.gray500),
                      const SizedBox(width: 2),
                      Text(
                        item.distanceKm != null
                            ? '${item.distanceKm!.toStringAsFixed(1)} km'
                            : 'Nearby',
                        style: const TextStyle(fontSize: 11, color: FromoColors.gray500),
                      ),
                      const SizedBox(width: 8),
                      const Icon(Icons.access_time, size: 12, color: FromoColors.gray500),
                      const SizedBox(width: 2),
                      Expanded(
                        child: Text(
                          _formatTime(event.startsAt),
                          style: const TextStyle(fontSize: 11, color: FromoColors.gray500),
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
                          color: event.isFree ? FromoColors.gray900 : FromoColors.green600,
                        ),
                      ),

                      const SizedBox(width: 6),

                      // Last-minute deal badge
                      if (event.isLastMinuteDeal)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
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
                      else if (event.spotsRemaining != null && event.spotsRemaining! <= 10)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
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
                        onTap: _openDirections,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: FromoColors.teal.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.directions, size: 13, color: FromoColors.teal),
                              SizedBox(width: 3),
                              Text(
                                'Directions',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: FromoColors.teal,
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

class _PulseEventPin extends StatefulWidget {
  final bool isSelected;
  final String priceLabel;
  final _CrowdBadgeData crowd;
  final int siblingCount;

  const _PulseEventPin({
    required this.isSelected,
    required this.priceLabel,
    required this.crowd,
    required this.siblingCount,
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
                color: widget.isSelected ? FromoColors.tealDark : FromoColors.teal,
                borderRadius: BorderRadius.circular(999),
                border: widget.isSelected ? Border.all(color: Colors.white, width: 2) : null,
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
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
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
          ],
        );
      },
    );
  }
}
