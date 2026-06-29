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
  final String? description;
  final String? category;
  final String venueId;
  // Only present on the organiser response; the public event payload omits it.
  final String? hostOrganisationId;
  final String status;
  final DateTime startsAt;
  final DateTime? endsAt;
  final int priceCents;
  final int? originalPriceCents;
  final int? capacity;
  final int? spotsRemaining;
  final String? aiSummary;
  final DateTime createdAt;

  const Event({
    required this.id,
    required this.title,
    this.description,
    this.category,
    required this.venueId,
    this.hostOrganisationId,
    required this.status,
    required this.startsAt,
    this.endsAt,
    required this.priceCents,
    this.originalPriceCents,
    this.capacity,
    this.spotsRemaining,
    this.aiSummary,
    required this.createdAt,
  });

  factory Event.fromJson(Map<String, dynamic> j) => Event(
        id: j['id'] as String,
        title: j['title'] as String,
        description: j['description'] as String?,
        category: j['category'] as String?,
        venueId: j['venue_id'] as String,
        hostOrganisationId: j['host_organisation_id'] as String?,
        status: j['status'] as String,
        startsAt: DateTime.parse(j['starts_at'] as String),
        endsAt: j['ends_at'] != null ? DateTime.parse(j['ends_at'] as String) : null,
        priceCents: j['price_cents'] as int,
        originalPriceCents: j['original_price_cents'] as int?,
        capacity: j['capacity'] as int?,
        spotsRemaining: j['spots_remaining'] as int?,
        aiSummary: j['ai_summary'] as String?,
        createdAt: DateTime.parse(j['created_at'] as String),
      );

  String get priceDisplay =>
      priceCents == 0 ? 'Free' : '\$${(priceCents / 100).toStringAsFixed(2)}';

  String? get originalPriceDisplay => originalPriceCents == null
      ? null
      : '\$${(originalPriceCents! / 100).toStringAsFixed(2)}';

  bool get isFree => priceCents == 0;
  bool get isLastMinuteDeal =>
      originalPriceCents != null && originalPriceCents! > priceCents;

  /// Mirrors the backend booking rule: an event can't be booked once it has
  /// ended (or, when there's no end time, once it has started).
  bool get isPast {
    final now = DateTime.now();
    final cutoff = endsAt ?? startsAt;
    return !cutoff.isAfter(now);
  }
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
