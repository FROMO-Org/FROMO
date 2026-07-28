import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/features/map/map_providers.dart';
import 'package:fromo/features/map/map_screen.dart';
import 'package:fromo/shared/models/event.dart';
import 'package:latlong2/latlong.dart';

void main() {
  testWidgets('event card keeps Directions visible on a narrow screen', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(360, 800);
    addTearDown(tester.view.reset);

    final now = DateTime.now();
    final item = EventListItem(
      event: Event(
        id: 'event-1',
        title: 'A deliberately long event title for a narrow mobile card',
        description: 'A long description that should truncate safely',
        category: 'Music',
        venueId: 'venue-1',
        status: 'active',
        startsAt: now.add(const Duration(hours: 1)),
        endsAt: now.add(const Duration(hours: 3)),
        priceCents: 98765,
        originalPriceCents: 123456,
        capacity: 100,
        spotsRemaining: 4,
        createdAt: now,
      ),
      distanceKm: 0.2,
      venue: const VenueSummary(
        id: 'venue-1',
        name: 'A venue with a long name',
        lat: 40.7580,
        lng: -73.9855,
      ),
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          locationProvider.overrideWith(
            (ref) => _FixedLocationNotifier(const LatLng(40.7580, -73.9855)),
          ),
          cityNameProvider.overrideWith((ref) async => 'New York'),
          busynessAreasProvider.overrideWith((ref) async => []),
          eventFeedPageProvider.overrideWith(
            (ref, request) async =>
                EventFeedPage(items: [item], hasMore: false),
          ),
        ],
        child: MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: const TextScaler.linear(1.3)),
            child: child!,
          ),
          home: const MapScreen(),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.text('Directions'), findsOneWidget);
    expect(find.text('Last-minute deal'), findsOneWidget);
  });
}

class _FixedLocationNotifier extends LocationNotifier {
  _FixedLocationNotifier(LatLng position) {
    state = LocationState(position: position);
  }

  @override
  Future<void> requestLocation() async {}
}
