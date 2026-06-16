import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';
import '../../core/theme.dart';
import '../../shared/models/event.dart';
import 'map_providers.dart';

const _filterCategories = ['All', 'Food', 'Music', 'Sports', 'Nightlife', 'Outdoors', 'Study'];

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  final _mapController = MapController();
  String? _selectedEventId;
  String _activeFilter = 'All';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(locationProvider.notifier).requestLocation();
    });
  }

  @override
  void dispose() {
    _mapController.dispose();
    super.dispose();
  }

  List<EventListItem> _applyFilter(List<EventListItem> items) {
    if (_activeFilter == 'All') return items;
    // Category filter will work once events have a category field from the API
    return items;
  }

  @override
  Widget build(BuildContext context) {
    final locationState = ref.watch(locationProvider);
    final eventsAsync = ref.watch(nearbyEventsProvider);

    return Scaffold(
      body: Stack(
        children: [
          // ── Map ───────────────────────────────────────────────────────────
          Positioned.fill(
            bottom: MediaQuery.of(context).size.height * 0.45,
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: locationState.position ?? const LatLng(53.3498, -6.2603),
                initialZoom: 14,
                onTap: (_, _) => setState(() => _selectedEventId = null),
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                  subdomains: const ['a', 'b', 'c', 'd'],
                  userAgentPackageName: 'com.fromo.fromo',
                ),
                if (locationState.position != null)
                  MarkerLayer(markers: [_buildLocationDot(locationState.position!)]),
                eventsAsync.when(
                  data: (items) => MarkerLayer(
                    markers: _applyFilter(items).map(_buildEventPin).toList(),
                  ),
                  loading: () => const MarkerLayer(markers: []),
                  error: (_, _) => const MarkerLayer(markers: []),
                ),
              ],
            ),
          ),

          // ── Top bar ───────────────────────────────────────────────────────
          SafeArea(
            child: _TopBar(
              onFilterTap: () {},
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
                onEventTap: (item) => context.push('/events/${item.event.id}'),
                onPinTap: (item) {
                  setState(() => _selectedEventId = item.event.id);
                  _mapController.move(LatLng(item.venue.lat, item.venue.lng), 15);
                },
                applyFilter: _applyFilter,
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

  Marker _buildEventPin(EventListItem item) {
    final isSelected = _selectedEventId == item.event.id;
    return Marker(
      point: LatLng(item.venue.lat, item.venue.lng),
      width: isSelected ? 84 : 72,
      height: 34,
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedEventId = item.event.id);
          _mapController.move(LatLng(item.venue.lat, item.venue.lng), 15);
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: isSelected ? FromoColors.tealDark : FromoColors.teal,
            borderRadius: BorderRadius.circular(20),
            border: isSelected ? Border.all(color: Colors.white, width: 2) : null,
            boxShadow: [
              BoxShadow(
                color: FromoColors.teal.withValues(alpha: isSelected ? 0.5 : 0.3),
                blurRadius: isSelected ? 10 : 4,
              ),
            ],
          ),
          child: Text(
            item.event.priceDisplay,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ),
    );
  }
}

// ── Top bar ────────────────────────────────────────────────────────────────────

class _TopBar extends StatelessWidget {
  final VoidCallback onFilterTap;
  final VoidCallback onLocationTap;

  const _TopBar({required this.onFilterTap, required this.onLocationTap});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          // Location chip
          Expanded(
            child: Material(
              elevation: 2,
              borderRadius: BorderRadius.circular(12),
              color: Colors.white,
              child: InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: onLocationTap,
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  child: Row(
                    children: [
                      Icon(Icons.location_on, color: FromoColors.teal, size: 18),
                      SizedBox(width: 6),
                      Text(
                        'Dublin, Ireland',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: FromoColors.gray900,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Filter button
          Material(
            elevation: 2,
            borderRadius: BorderRadius.circular(12),
            color: Colors.white,
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: onFilterTap,
              child: const Padding(
                padding: EdgeInsets.all(12),
                child: Icon(Icons.tune, color: FromoColors.gray700, size: 22),
              ),
            ),
          ),
        ],
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
  final ValueChanged<EventListItem> onEventTap;
  final ValueChanged<EventListItem> onPinTap;
  final List<EventListItem> Function(List<EventListItem>) applyFilter;

  const _BottomPanel({
    required this.scrollController,
    required this.activeFilter,
    required this.onFilterChanged,
    required this.eventsAsync,
    required this.selectedEventId,
    required this.onEventTap,
    required this.onPinTap,
    required this.applyFilter,
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
                        Text('Try adjusting your filters', style: TextStyle(color: FromoColors.gray500, fontSize: 12)),
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
                  itemBuilder: (_, i) => _ActivityCard(
                    item: filtered[i],
                    isSelected: selectedEventId == filtered[i].event.id,
                    onTap: () => onEventTap(filtered[i]),
                  ),
                ),
              );
            },
            loading: () => const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => SliverFillRemaining(
              child: Center(child: Text('Error: $e')),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Activity card ──────────────────────────────────────────────────────────────

class _ActivityCard extends StatelessWidget {
  final EventListItem item;
  final bool isSelected;
  final VoidCallback onTap;

  const _ActivityCard({required this.item, required this.isSelected, required this.onTap});

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
            // Image placeholder (will be real image when we have image URLs)
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
                  // Title + accessibility icon
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
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
                      ),
                    ],
                  ),

                  const SizedBox(height: 4),

                  // Venue name
                  Text(
                    item.venue.name,
                    style: const TextStyle(fontSize: 12, color: FromoColors.gray500),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),

                  const SizedBox(height: 6),

                  // Distance + time row
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

                  // Price row
                  Row(
                    children: [
                      Text(
                        event.priceDisplay,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: event.isFree ? FromoColors.gray900 : FromoColors.green600,
                        ),
                      ),
                      const SizedBox(width: 6),
                      // Spots remaining badge
                      if (event.spotsRemaining != null && event.spotsRemaining! <= 10)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
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
