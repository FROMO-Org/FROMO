class VenueSummary {
  final String id;
  final String name;
  final double lat;
  final double lng;

  const VenueSummary({required this.id, required this.name, required this.lat, required this.lng});

  factory VenueSummary.fromJson(Map<String, dynamic> j) => VenueSummary(
        id: j['id'] as String,
        name: j['name'] as String,
        lat: (j['lat'] as num).toDouble(),
        lng: (j['lng'] as num).toDouble(),
      );
}

class Event {
  final String id;
  final String title;
  final String venueId;
  final String hostOrganisationId;
  final String status;
  final DateTime startsAt;
  final DateTime? endsAt;
  final int priceCents;
  final int? capacity;
  final int? spotsRemaining;
  final DateTime createdAt;

  const Event({
    required this.id,
    required this.title,
    required this.venueId,
    required this.hostOrganisationId,
    required this.status,
    required this.startsAt,
    this.endsAt,
    required this.priceCents,
    this.capacity,
    this.spotsRemaining,
    required this.createdAt,
  });

  factory Event.fromJson(Map<String, dynamic> j) => Event(
        id: j['id'] as String,
        title: j['title'] as String,
        venueId: j['venue_id'] as String,
        hostOrganisationId: j['host_organisation_id'] as String,
        status: j['status'] as String,
        startsAt: DateTime.parse(j['starts_at'] as String),
        endsAt: j['ends_at'] != null ? DateTime.parse(j['ends_at'] as String) : null,
        priceCents: j['price_cents'] as int,
        capacity: j['capacity'] as int?,
        spotsRemaining: j['spots_remaining'] as int?,
        createdAt: DateTime.parse(j['created_at'] as String),
      );

  String get priceDisplay =>
      priceCents == 0 ? 'Free' : '\$${(priceCents / 100).toStringAsFixed(2)}';

  bool get isFree => priceCents == 0;
}

class EventListItem {
  final Event event;
  final double? distanceKm;
  final VenueSummary venue;

  const EventListItem({required this.event, this.distanceKm, required this.venue});

  factory EventListItem.fromJson(Map<String, dynamic> j) => EventListItem(
        event: Event.fromJson(j['event'] as Map<String, dynamic>),
        distanceKm: (j['distance_km'] as num?)?.toDouble(),
        venue: VenueSummary.fromJson(j['venue'] as Map<String, dynamic>),
      );
}
