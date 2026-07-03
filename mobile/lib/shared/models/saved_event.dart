import 'event.dart';

class SavedEvent {
  final String eventId;
  final DateTime savedAt;

  const SavedEvent({required this.eventId, required this.savedAt});

  factory SavedEvent.fromJson(Map<String, dynamic> j) => SavedEvent(
        eventId: j['event_id'] as String,
        savedAt: DateTime.parse(j['saved_at'] as String),
      );
}

class SavedEventListItem {
  final SavedEvent savedEvent;
  final Event event;
  final VenueSummary venue;

  const SavedEventListItem({
    required this.savedEvent,
    required this.event,
    required this.venue,
  });

  factory SavedEventListItem.fromJson(Map<String, dynamic> j) => SavedEventListItem(
        savedEvent: SavedEvent.fromJson(j['saved_event'] as Map<String, dynamic>),
        event: Event.fromJson(j['event'] as Map<String, dynamic>),
        venue: VenueSummary.fromJson(j['venue'] as Map<String, dynamic>),
      );
}
