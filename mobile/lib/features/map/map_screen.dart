import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';
import '../../core/theme.dart';
import '../../shared/models/event.dart';
import 'map_providers.dart';

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  final _mapController = MapController();
  String? _selectedEventId;

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

  @override
  Widget build(BuildContext context) {
    final locationState = ref.watch(locationProvider);
    final eventsAsync = ref.watch(nearbyEventsProvider);

    return Scaffold(
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter:
                  locationState.position ?? const LatLng(53.3498, -6.2603),
              initialZoom: 14,
              onTap: (_, _) => setState(() => _selectedEventId = null),
            ),
            children: [
              TileLayer(
                urlTemplate:
                    'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                subdomains: const ['a', 'b', 'c', 'd'],
                userAgentPackageName: 'com.fromo.fromo',
              ),
              // User location blue dot
              if (locationState.position != null)
                MarkerLayer(
                  markers: [_buildLocationMarker(locationState.position!)],
                ),
              // Event pins
              eventsAsync.when(
                data: (items) => MarkerLayer(
                  markers: items.map((item) => _buildEventPin(item)).toList(),
                ),
                loading: () => const MarkerLayer(markers: []),
                error: (_, _) => const MarkerLayer(markers: []),
              ),
            ],
          ),

          // Top bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: _TopBar(
                onLocationTap: () {
                  final pos = ref.read(locationProvider).position;
                  if (pos != null) _mapController.move(pos, 14);
                },
              ),
            ),
          ),

          // Bottom event list panel
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: _EventListPanel(
              eventsAsync: eventsAsync,
              selectedEventId: _selectedEventId,
              onEventTap: (item) => context.push('/events/${item.event.id}'),
            ),
          ),

          // Loading indicator
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

  Marker _buildLocationMarker(LatLng pos) {
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
              color: Colors.blue.withValues(alpha: 0.4),
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
      width: isSelected ? 80 : 70,
      height: isSelected ? 36 : 32,
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedEventId = item.event.id);
          _mapController.move(LatLng(item.venue.lat, item.venue.lng), 15);
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: isSelected ? FromoColors.tealDark : FromoColors.teal,
            borderRadius: BorderRadius.circular(20),
            border: isSelected
                ? Border.all(color: Colors.white, width: 2)
                : null,
            boxShadow: [
              BoxShadow(
                color: FromoColors.teal.withValues(alpha: 0.4),
                blurRadius: isSelected ? 8 : 4,
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

class _TopBar extends StatelessWidget {
  final VoidCallback onLocationTap;
  const _TopBar({required this.onLocationTap});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Material(
            elevation: 2,
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () {},
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 12,
                ),
                child: Row(
                  children: [
                    Icon(Icons.search, color: FromoColors.gray500, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Search events...',
                      style: TextStyle(color: FromoColors.gray500),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Material(
          elevation: 2,
          borderRadius: BorderRadius.circular(12),
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: onLocationTap,
            child: const Padding(
              padding: EdgeInsets.all(12),
              child: Icon(Icons.my_location, color: FromoColors.teal),
            ),
          ),
        ),
      ],
    );
  }
}

class _EventListPanel extends StatelessWidget {
  final AsyncValue<List<EventListItem>> eventsAsync;
  final String? selectedEventId;
  final ValueChanged<EventListItem> onEventTap;

  const _EventListPanel({
    required this.eventsAsync,
    required this.selectedEventId,
    required this.onEventTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 200,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        children: [
          const _DragHandle(),
          Expanded(
            child: eventsAsync.when(
              data: (items) => items.isEmpty
                  ? const Center(child: Text('No events nearby'))
                  : ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                      itemCount: items.length,
                      separatorBuilder: (_, _) => const SizedBox(width: 12),
                      itemBuilder: (context, i) => _EventCard(
                        item: items[i],
                        isSelected: selectedEventId == items[i].event.id,
                        onTap: () => onEventTap(items[i]),
                      ),
                    ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error loading events: $e')),
            ),
          ),
        ],
      ),
    );
  }
}

class _DragHandle extends StatelessWidget {
  const _DragHandle();
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Container(
        width: 48,
        height: 4,
        decoration: BoxDecoration(
          color: FromoColors.gray200,
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }
}

class _EventCard extends StatelessWidget {
  final EventListItem item;
  final bool isSelected;
  final VoidCallback onTap;

  const _EventCard({
    required this.item,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: 220,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? FromoColors.teal : FromoColors.gray200,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 4,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              item.event.title,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: FromoColors.gray900,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Text(
              item.venue.name,
              style: const TextStyle(fontSize: 12, color: FromoColors.gray500),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const Spacer(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  item.event.priceDisplay,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: FromoColors.green600,
                  ),
                ),
                if (item.distanceKm != null)
                  Text(
                    '${item.distanceKm!.toStringAsFixed(1)} km',
                    style: const TextStyle(
                      fontSize: 12,
                      color: FromoColors.gray500,
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
