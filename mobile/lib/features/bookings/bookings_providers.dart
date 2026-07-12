import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../shared/models/booking.dart';

/// The current user's bookings (confirmed + cancelled), as returned by
/// `GET /bookings/me` — each row is `{ booking, event, venue }`.
final myBookingsProvider =
    FutureProvider.autoDispose<List<BookingListItem>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final res = await api.get<List<dynamic>>('/bookings/me');
  return (res.data ?? [])
      .cast<Map<String, dynamic>>()
      .map(BookingListItem.fromJson)
      .toList();
});

final bookingActionsProvider =
    Provider<BookingActions>((ref) => BookingActions(ref));

class BookingActions {
  final Ref _ref;
  BookingActions(this._ref);

  /// Cancels a booking (`PATCH /bookings/{id}`). Throws on failure so the UI can
  /// surface the backend message.
  Future<void> cancel(String bookingId) async {
    await _ref.read(apiClientProvider).patch('/bookings/$bookingId');
    _ref.invalidate(myBookingsProvider);
  }
}
