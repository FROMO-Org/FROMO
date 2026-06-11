import 'event.dart';

class Booking {
  final String id;
  final String userId;
  final String eventId;
  final int quantity;
  final int totalPriceCents;
  final String status;
  final DateTime createdAt;
  final DateTime? cancelledAt;

  const Booking({
    required this.id,
    required this.userId,
    required this.eventId,
    required this.quantity,
    required this.totalPriceCents,
    required this.status,
    required this.createdAt,
    this.cancelledAt,
  });

  factory Booking.fromJson(Map<String, dynamic> j) => Booking(
        id: j['id'] as String,
        userId: j['user_id'] as String,
        eventId: j['event_id'] as String,
        quantity: j['quantity'] as int,
        totalPriceCents: j['total_price_cents'] as int,
        status: j['status'] as String,
        createdAt: DateTime.parse(j['created_at'] as String),
        cancelledAt: j['cancelled_at'] != null ? DateTime.parse(j['cancelled_at'] as String) : null,
      );

  bool get isConfirmed => status == 'confirmed';
}

class BookingListItem {
  final Booking booking;
  final Event event;
  final VenueSummary venue;

  const BookingListItem({required this.booking, required this.event, required this.venue});

  factory BookingListItem.fromJson(Map<String, dynamic> j) => BookingListItem(
        booking: Booking.fromJson(j['booking'] as Map<String, dynamic>),
        event: Event.fromJson(j['event'] as Map<String, dynamic>),
        venue: VenueSummary.fromJson(j['venue'] as Map<String, dynamic>),
      );
}
