import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../shared/models/booking.dart';
import 'bookings_providers.dart';

class BookingsScreen extends ConsumerWidget {
  const BookingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookingsAsync = ref.watch(myBookingsProvider);

    return Scaffold(
      backgroundColor: FromoColors.gray50,
      appBar: AppBar(title: const Text('My Bookings')),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(myBookingsProvider.future),
        child: bookingsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => const _Message(
            icon: Icons.error_outline,
            title: "Couldn't load your bookings",
            subtitle: 'Pull down to try again',
          ),
          data: (items) {
            if (items.isEmpty) {
              return const _Message(
                icon: Icons.confirmation_number_outlined,
                title: 'No bookings yet',
                subtitle: 'Book an event and it\'ll show up here',
              );
            }
            // Confirmed first, then cancelled; each group newest-booked first.
            final sorted = [...items]..sort((a, b) {
                if (a.booking.isConfirmed != b.booking.isConfirmed) {
                  return a.booking.isConfirmed ? -1 : 1;
                }
                return b.booking.bookedAt.compareTo(a.booking.bookedAt);
              });
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              itemCount: sorted.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (_, i) => _BookingCard(
                item: sorted[i],
                onTap: () => context.push('/events/${sorted[i].event.id}'),
                onCancel: () => _confirmCancel(context, ref, sorted[i]),
              ),
            );
          },
        ),
      ),
    );
  }

  Future<void> _confirmCancel(
      BuildContext context, WidgetRef ref, BookingListItem item) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cancel booking?'),
        content: Text('Cancel your booking for "${item.event.title}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Keep'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Cancel booking',
                style: TextStyle(color: Color(0xFFDC2626))),
          ),
        ],
      ),
    );
    if (ok != true) return;

    try {
      await ref.read(bookingActionsProvider).cancel(item.booking.id);
      if (context.mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(const SnackBar(content: Text('Booking cancelled')));
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(const SnackBar(content: Text('Could not cancel booking')));
      }
    }
  }
}

// ── Card ─────────────────────────────────────────────────────────────────────

class _BookingCard extends StatelessWidget {
  final BookingListItem item;
  final VoidCallback onTap;
  final VoidCallback onCancel;

  const _BookingCard({
    required this.item,
    required this.onTap,
    required this.onCancel,
  });

  @override
  Widget build(BuildContext context) {
    final booking = item.booking;
    final event = item.event;
    final cancelled = booking.isCancelled;

    return Opacity(
      opacity: cancelled ? 0.6 : 1,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.06),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      width: 64,
                      height: 64,
                      color: FromoColors.gray100,
                      child: const Icon(Icons.event,
                          color: FromoColors.gray500, size: 28),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                event.title,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 14,
                                  color: FromoColors.gray900,
                                  height: 1.3,
                                ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 6),
                            _StatusBadge(cancelled: cancelled),
                          ],
                        ),
                        const SizedBox(height: 3),
                        Text(
                          item.venue.name,
                          style: const TextStyle(
                              fontSize: 12, color: FromoColors.gray500),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            const Icon(Icons.access_time,
                                size: 12, color: FromoColors.gray500),
                            const SizedBox(width: 3),
                            Expanded(
                              child: Text(
                                _formatTime(event.startsAt),
                                style: const TextStyle(
                                    fontSize: 11, color: FromoColors.gray500),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              const Divider(height: 1, color: FromoColors.gray100),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(
                    '${booking.quantity} ${booking.quantity == 1 ? "ticket" : "tickets"}',
                    style: const TextStyle(
                        fontSize: 12, color: FromoColors.gray700),
                  ),
                  const SizedBox(width: 8),
                  Text('·',
                      style: TextStyle(color: FromoColors.gray500)),
                  const SizedBox(width: 8),
                  Text(
                    booking.totalPriceDisplay,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: booking.totalPriceCents == 0
                          ? FromoColors.gray900
                          : FromoColors.green600,
                    ),
                  ),
                  const Spacer(),
                  if (!cancelled)
                    TextButton(
                      onPressed: onCancel,
                      style: TextButton.styleFrom(
                        padding:
                            const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      child: const Text('Cancel',
                          style: TextStyle(
                              color: Color(0xFFDC2626), fontSize: 13)),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    final h = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
    final m = dt.minute.toString().padLeft(2, '0');
    final period = dt.hour < 12 ? 'AM' : 'PM';
    return '${months[dt.month - 1]} ${dt.day}, $h:$m $period';
  }
}

class _StatusBadge extends StatelessWidget {
  final bool cancelled;
  const _StatusBadge({required this.cancelled});

  @override
  Widget build(BuildContext context) {
    final color = cancelled ? const Color(0xFF991B1B) : FromoColors.green600;
    final bg = cancelled ? const Color(0xFFFEE2E2) : const Color(0xFFD1FAE5);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        cancelled ? 'Cancelled' : 'Confirmed',
        style: TextStyle(
            fontSize: 10, color: color, fontWeight: FontWeight.w600),
      ),
    );
  }
}

// ── Empty / error placeholder (scrollable so pull-to-refresh works) ───────────

class _Message extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  const _Message({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (_, constraints) => SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: ConstrainedBox(
          constraints: BoxConstraints(minHeight: constraints.maxHeight),
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 56, color: FromoColors.gray200),
                  const SizedBox(height: 14),
                  Text(title,
                      style: const TextStyle(
                          color: FromoColors.gray700, fontSize: 15)),
                  const SizedBox(height: 4),
                  Text(subtitle,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          color: FromoColors.gray500, fontSize: 12)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
