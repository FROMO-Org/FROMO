import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/shared/models/event.dart';

void main() {
  group('Event model', () {
    test('fromJson parses url, ai summary, dates, and prices', () {
      final event = Event.fromJson({
        'id': 'event-1',
        'title': 'Jazz Night',
        'description': 'Live music',
        'url': 'https://example.com/event',
        'image_url': 'https://example.com/event.jpg',
        'category': 'Music',
        'venue_id': 'venue-1',
        'host_organisation_id': 'org-1',
        'status': 'active',
        'starts_at': '2026-07-10T18:00:00Z',
        'ends_at': '2026-07-10T20:30:00Z',
        'price_cents': 1200,
        'original_price_cents': 1800,
        'capacity': 100,
        'spots_remaining': 25,
        'ai_summary': 'A lively evening with local bands.',
        'created_at': '2026-07-01T12:00:00Z',
      });

      expect(event.id, 'event-1');
      expect(event.url, 'https://example.com/event');
      expect(event.imageUrl, 'https://example.com/event.jpg');
      expect(event.aiSummary, 'A lively evening with local bands.');
      expect(event.startsAt, DateTime.parse('2026-07-10T18:00:00Z'));
      expect(event.endsAt, DateTime.parse('2026-07-10T20:30:00Z'));
      expect(event.priceDisplay, '\$12.00');
      expect(event.originalPriceDisplay, '\$18.00');
      expect(event.isLastMinuteDeal, isTrue);
    });

    test('isPast uses endsAt when present', () {
      final event = Event(
        id: 'event-2',
        title: 'Past event',
        venueId: 'venue-1',
        status: 'active',
        startsAt: DateTime.now().subtract(const Duration(hours: 3)),
        endsAt: DateTime.now().subtract(const Duration(hours: 1)),
        priceCents: 0,
        createdAt: DateTime.now(),
      );

      expect(event.isPast, isTrue);
    });

    test('isPast uses startsAt when endsAt is absent', () {
      final futureEvent = Event(
        id: 'event-3',
        title: 'Future event',
        venueId: 'venue-1',
        status: 'active',
        startsAt: DateTime.now().add(const Duration(hours: 2)),
        endsAt: null,
        priceCents: 0,
        createdAt: DateTime.now(),
      );

      expect(futureEvent.isPast, isFalse);
    });
  });
}
