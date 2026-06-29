import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../shared/models/event.dart';
import '../../shared/models/venue.dart';

/// Combines an event with its full venue. `GET /events/{id}` returns only a
/// `venue_id`, so we fetch the venue separately to get the address/accessibility
/// the list payload doesn't carry.
class EventDetail {
  final Event event;
  final Venue venue;
  const EventDetail({required this.event, required this.venue});
}

final eventDetailProvider =
    FutureProvider.autoDispose.family<EventDetail, String>((ref, eventId) async {
  final api = ref.watch(apiClientProvider);

  final eventRes = await api.get<Map<String, dynamic>>('/events/$eventId');
  final event = Event.fromJson(eventRes.data!);

  final venueRes = await api.get<Map<String, dynamic>>('/venues/${event.venueId}');
  final venue = Venue.fromJson(venueRes.data!);

  return EventDetail(event: event, venue: venue);
});

/// The current user's saved events, newest API order. Backs the Saved tab.
/// Each `MySavedEventResponse` row is `{ saved_event, event, venue }`, which
/// `EventListItem.fromJson` reads directly (distance_km is simply absent → null).
final savedEventsProvider =
    FutureProvider.autoDispose<List<EventListItem>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final res = await api.get<List<dynamic>>('/saved-events/me');
  return (res.data ?? [])
      .cast<Map<String, dynamic>>()
      .map(EventListItem.fromJson)
      .toList();
});

/// The set of saved event ids, derived from [savedEventsProvider] so the detail
/// screen's bookmark state and the Saved tab never drift apart.
final savedEventIdsProvider = FutureProvider.autoDispose<Set<String>>((ref) async {
  try {
    final items = await ref.watch(savedEventsProvider.future);
    return items.map((i) => i.event.id).toSet();
  } catch (_) {
    // Not logged in / endpoint unreachable — treat as nothing saved.
    return <String>{};
  }
});

/// Booking + save/unsave actions for the detail screen.
final eventActionsProvider = Provider<EventActions>((ref) => EventActions(ref));

class EventActions {
  final Ref _ref;
  EventActions(this._ref);

  ApiClient get _api => _ref.read(apiClientProvider);

  /// Books [quantity] spots. Returns when the booking is confirmed; throws on
  /// failure (e.g. 409 already booked / sold out) so the UI can surface it.
  Future<void> book(String eventId, {int quantity = 1}) async {
    await _api.post('/bookings/', data: {'event_id': eventId, 'quantity': quantity});
    // Spots remaining changed — refresh the detail view.
    _ref.invalidate(eventDetailProvider(eventId));
  }

  Future<void> save(String eventId) async {
    await _api.post('/saved-events/', data: {'event_id': eventId});
    _ref.invalidate(savedEventsProvider);
  }

  Future<void> unsave(String eventId) async {
    await _api.delete('/saved-events/$eventId');
    _ref.invalidate(savedEventsProvider);
  }
}
