import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme.dart';
import '../../shared/models/event.dart';
import '../../shared/models/venue.dart';
import 'event_detail_providers.dart';

class EventDetailScreen extends ConsumerStatefulWidget {
  final String eventId;
  const EventDetailScreen({super.key, required this.eventId});

  @override
  ConsumerState<EventDetailScreen> createState() => _EventDetailScreenState();
}

class _EventDetailScreenState extends ConsumerState<EventDetailScreen> {
  bool _booking = false;
  bool _booked = false; // set after a successful (or already-existing) booking

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(eventDetailProvider(widget.eventId));

    return Scaffold(
      backgroundColor: FromoColors.gray50,
      body: detailAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorView(
          onBack: () => Navigator.of(context).maybePop(),
          onRetry: () => ref.invalidate(eventDetailProvider(widget.eventId)),
        ),
        data: (detail) => _Content(
          detail: detail,
          booking: _booking,
          booked: _booked,
          isSaved: ref
                  .watch(savedEventIdsProvider)
                  .valueOrNull
                  ?.contains(detail.event.id) ??
              false,
          onBack: () => Navigator.of(context).maybePop(),
          onToggleSave: () => _toggleSave(detail.event.id),
          onBook: () => _book(detail.event),
        ),
      ),
    );
  }

  Future<void> _toggleSave(String eventId) async {
    final saved = ref.read(savedEventIdsProvider).valueOrNull?.contains(eventId) ?? false;
    final actions = ref.read(eventActionsProvider);
    try {
      if (saved) {
        await actions.unsave(eventId);
      } else {
        await actions.save(eventId);
      }
    } catch (e) {
      if (mounted) _snack(_messageFor(e, fallback: 'Could not update saved events'));
    }
  }

  Future<void> _book(Event event) async {
    if (_booking || _booked) return;
    setState(() => _booking = true);
    try {
      await ref.read(eventActionsProvider).book(event.id);
      if (!mounted) return;
      setState(() => _booked = true);
      _snack(event.isFree ? 'You\'re going! 🎉' : 'Booked! 🎉');
    } on DioException catch (e) {
      if (!mounted) return;
      // 409 = already booked: treat as success so the button reflects reality.
      if (e.response?.statusCode == 409 &&
          (e.response?.data is Map &&
              (e.response?.data['detail'] as String?)?.contains('already') == true)) {
        setState(() => _booked = true);
      }
      _snack(_messageFor(e, fallback: 'Could not complete booking'));
    } catch (e) {
      if (mounted) _snack(_messageFor(e, fallback: 'Could not complete booking'));
    } finally {
      if (mounted) setState(() => _booking = false);
    }
  }

  String _messageFor(Object e, {required String fallback}) {
    if (e is DioException) {
      final detail = e.response?.data;
      if (detail is Map && detail['detail'] is String) return detail['detail'] as String;
    }
    return fallback;
  }

  void _snack(String msg) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(msg)));
  }
}

// ── Content ──────────────────────────────────────────────────────────────────

class _Content extends StatelessWidget {
  final EventDetail detail;
  final bool isSaved;
  final bool booking;
  final bool booked;
  final VoidCallback onBack;
  final VoidCallback onToggleSave;
  final VoidCallback onBook;

  const _Content({
    required this.detail,
    required this.isSaved,
    required this.booking,
    required this.booked,
    required this.onBack,
    required this.onToggleSave,
    required this.onBook,
  });

  @override
  Widget build(BuildContext context) {
    final event = detail.event;
    final venue = detail.venue;

    return Stack(
      children: [
        CustomScrollView(
          slivers: [
            _HeaderImage(onBack: onBack, isSaved: isSaved, onToggleSave: onToggleSave),
            SliverToBoxAdapter(
              child: Container(
                decoration: const BoxDecoration(
                  color: FromoColors.gray50,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                ),
                transform: Matrix4.translationValues(0, -20, 0),
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 140),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (event.category != null && event.category!.isNotEmpty)
                      _CategoryChip(label: event.category!),
                    const SizedBox(height: 12),
                    Text(
                      event.title,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w700,
                        color: FromoColors.gray900,
                        height: 1.25,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _InfoRow(
                      icon: Icons.calendar_today_outlined,
                      title: _formatDate(event.startsAt),
                      subtitle: _timeRange(event.startsAt, event.endsAt),
                    ),
                    const SizedBox(height: 12),
                    _InfoRow(
                      icon: Icons.location_on_outlined,
                      title: venue.name,
                      subtitle: (venue.address?.isNotEmpty ?? false)
                          ? venue.address
                          : null,
                      trailing: _DirectionsButton(venue: venue),
                    ),
                    if (event.spotsRemaining != null) ...[
                      const SizedBox(height: 12),
                      _InfoRow(
                        icon: Icons.people_outline,
                        title: event.spotsRemaining! > 0
                            ? '${event.spotsRemaining} spots left'
                            : 'Sold out',
                        subtitle: event.capacity != null
                            ? 'of ${event.capacity} total'
                            : null,
                      ),
                    ],
                    if (venue.isAccessible) ...[
                      const SizedBox(height: 12),
                      const _InfoRow(
                        icon: Icons.accessible_outlined,
                        title: 'Wheelchair accessible',
                      ),
                    ],
                    if (event.description != null && event.description!.isNotEmpty) ...[
                      const SizedBox(height: 24),
                      const _SectionTitle('About'),
                      const SizedBox(height: 8),
                      Text(
                        event.description!,
                        style: const TextStyle(
                          fontSize: 15,
                          height: 1.5,
                          color: FromoColors.gray700,
                        ),
                      ),
                    ],
                    if (event.aiSummary != null && event.aiSummary!.trim().isNotEmpty) ...[
                      const SizedBox(height: 24),
                      const _SectionTitle('AI Summary'),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: FromoColors.teal.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: FromoColors.teal.withValues(alpha: 0.15),
                          ),
                        ),
                        child: Text(
                          event.aiSummary!.trim(),
                          style: const TextStyle(
                            fontSize: 14,
                            height: 1.5,
                            color: FromoColors.gray700,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),

        // Pinned booking bar
        Align(
          alignment: Alignment.bottomCenter,
          child: _BookingBar(
            event: event,
            booking: booking,
            booked: booked,
            onBook: onBook,
          ),
        ),
      ],
    );
  }
}

// ── Header image ─────────────────────────────────────────────────────────────

class _HeaderImage extends StatelessWidget {
  final VoidCallback onBack;
  final bool isSaved;
  final VoidCallback onToggleSave;

  const _HeaderImage({
    required this.onBack,
    required this.isSaved,
    required this.onToggleSave,
  });

  @override
  Widget build(BuildContext context) {
    return SliverAppBar(
      pinned: false,
      expandedHeight: 220,
      automaticallyImplyLeading: false,
      backgroundColor: FromoColors.teal,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [FromoColors.teal, FromoColors.tealDark],
            ),
          ),
          child: const Center(
            child: Icon(Icons.event, size: 72, color: Colors.white54),
          ),
        ),
      ),
      leading: Padding(
        padding: const EdgeInsets.all(8),
        child: _CircleButton(icon: Icons.arrow_back, onTap: onBack),
      ),
      actions: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: _CircleButton(
            icon: isSaved ? Icons.bookmark : Icons.bookmark_outline,
            onTap: onToggleSave,
          ),
        ),
      ],
    );
  }
}

class _CircleButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _CircleButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      shape: const CircleBorder(),
      elevation: 2,
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Icon(icon, size: 20, color: FromoColors.gray900),
        ),
      ),
    );
  }
}

// ── Small building blocks ────────────────────────────────────────────────────

class _CategoryChip extends StatelessWidget {
  final String label;
  const _CategoryChip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: FromoColors.teal.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: FromoColors.tealDark,
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 17,
        fontWeight: FontWeight.w700,
        color: FromoColors.gray900,
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;

  const _InfoRow({
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: FromoColors.gray200),
          ),
          child: Icon(icon, size: 20, color: FromoColors.teal),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: FromoColors.gray900,
                ),
              ),
              if (subtitle != null && subtitle!.isNotEmpty) ...[
                const SizedBox(height: 2),
                Text(
                  subtitle!,
                  style: const TextStyle(fontSize: 12, color: FromoColors.gray500),
                ),
              ],
            ],
          ),
        ),
        ?trailing,
      ],
    );
  }
}

class _DirectionsButton extends StatelessWidget {
  final Venue venue;
  const _DirectionsButton({required this.venue});

  Future<void> _open() async {
    final uri = Uri.parse(
      'https://www.google.com/maps/dir/?api=1'
      '&destination=${venue.lat},${venue.lng}&travelmode=transit',
    );
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return TextButton.icon(
      onPressed: _open,
      icon: const Icon(Icons.directions, size: 18, color: FromoColors.teal),
      label: const Text('Directions', style: TextStyle(color: FromoColors.teal)),
      style: TextButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 8),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }
}

// ── Booking bar ──────────────────────────────────────────────────────────────

class _BookingBar extends StatelessWidget {
  final Event event;
  final bool booking;
  final bool booked;
  final VoidCallback onBook;

  const _BookingBar({
    required this.event,
    required this.booking,
    required this.booked,
    required this.onBook,
  });

  @override
  Widget build(BuildContext context) {
    final soldOut = event.spotsRemaining != null && event.spotsRemaining! <= 0;
    final ended = event.isPast;
    final unavailable = event.status != 'active';
    final disabled = booking || booked || soldOut || unavailable || ended;

    final String label;
    if (booked) {
      label = 'Booked ✓';
    } else if (ended) {
      label = 'Event has ended';
    } else if (unavailable) {
      label = 'Unavailable';
    } else if (soldOut) {
      label = 'Sold out';
    } else if (event.isFree) {
      label = 'Reserve a spot';
    } else {
      label = 'Book now';
    }

    return Container(
      padding: EdgeInsets.fromLTRB(20, 12, 20, 12 + MediaQuery.of(context).padding.bottom),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 12,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: Row(
        children: [
          // Price
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              if (event.isLastMinuteDeal)
                Text(
                  event.originalPriceDisplay!,
                  style: const TextStyle(
                    fontSize: 12,
                    color: FromoColors.gray500,
                    decoration: TextDecoration.lineThrough,
                  ),
                ),
              Text(
                event.priceDisplay,
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: event.isFree ? FromoColors.gray900 : FromoColors.green600,
                ),
              ),
            ],
          ),
          const SizedBox(width: 16),
          // Book button
          Expanded(
            child: ElevatedButton(
              onPressed: disabled ? null : onBook,
              child: booking
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(label),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Error view ───────────────────────────────────────────────────────────────

class _ErrorView extends StatelessWidget {
  final VoidCallback onBack;
  final VoidCallback onRetry;
  const _ErrorView({required this.onBack, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Stack(
        children: [
          Align(
            alignment: Alignment.topLeft,
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: _CircleButton(icon: Icons.arrow_back, onTap: onBack),
            ),
          ),
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline, size: 48, color: FromoColors.gray500),
                const SizedBox(height: 12),
                const Text("Couldn't load this event",
                    style: TextStyle(color: FromoColors.gray700)),
                const SizedBox(height: 12),
                OutlinedButton(onPressed: onRetry, child: const Text('Try again')),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Date/time formatting ─────────────────────────────────────────────────────

const _months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];
const _weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

String _formatDate(DateTime dt) =>
    '${_weekdays[dt.weekday - 1]}, ${_months[dt.month - 1]} ${dt.day}';

String _timeRange(DateTime start, DateTime? end) {
  final s = _hm(start);
  if (end == null) return s;
  return '$s – ${_hm(end)}';
}

String _hm(DateTime dt) {
  final h = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
  final m = dt.minute.toString().padLeft(2, '0');
  final period = dt.hour < 12 ? 'AM' : 'PM';
  return '$h:$m $period';
}
