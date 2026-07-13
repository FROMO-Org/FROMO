import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/core/api_client.dart';
import 'package:fromo/features/bookings/bookings_providers.dart';

import '../mocks/mock_api_client.dart';

void main() {
  test('myBookingsProvider parses mocked API response', () async {
    final api = FakeApiClient(
      onGet: (path, params) async {
        expect(path, '/bookings/me');
        return Response<dynamic>(
          requestOptions: RequestOptions(path: path),
          data: [
            {
              'booking': {
                'id': 'booking-1',
                'event_id': 'event-1',
                'quantity': 2,
                'total_price_cents': 2400,
                'status': 'confirmed',
                'booked_at': '2026-07-10T12:00:00Z',
                'cancelled_at': null,
              },
              'event': {
                'id': 'event-1',
                'title': 'Jazz Night',
                'description': 'Live music',
                'url': 'https://example.com',
                'image_url': 'https://example.com/event.jpg',
                'category': 'Music',
                'venue_id': 'venue-1',
                'status': 'active',
                'starts_at': '2026-07-10T18:00:00Z',
                'ends_at': '2026-07-10T20:00:00Z',
                'price_cents': 1200,
                'original_price_cents': null,
                'capacity': 100,
                'spots_remaining': 20,
                'ai_summary': 'Summary',
                'created_at': '2026-07-01T12:00:00Z',
              },
              'venue': {
                'id': 'venue-1',
                'name': 'Union Hall',
                'lat': 40.7,
                'lng': -73.9,
              },
            },
          ],
          statusCode: 200,
        );
      },
    );

    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(api),
      ],
    );
    addTearDown(container.dispose);

    final bookings = await container.read(myBookingsProvider.future);

    expect(bookings, hasLength(1));
    expect(bookings.single.booking.totalPriceDisplay, '\$24.00');
    expect(bookings.single.event.title, 'Jazz Night');
    expect(bookings.single.venue.name, 'Union Hall');
  });
}
