import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../shared/models/event.dart';
import '../../shared/widgets/event_thumbnail.dart';
import '../events/event_detail_providers.dart';

class SavedScreen extends ConsumerWidget {
  const SavedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final savedAsync = ref.watch(savedEventsProvider);

    return Scaffold(
      backgroundColor: FromoColors.gray50,
      appBar: AppBar(title: const Text('Saved Events')),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(savedEventsProvider.future),
        child: savedAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => _Message(
            scrollable: true,
            icon: Icons.error_outline,
            title: "Couldn't load saved events",
            subtitle: 'Pull down to try again',
          ),
          data: (items) {
            if (items.isEmpty) {
              return const _Message(
                scrollable: true,
                icon: Icons.bookmark_outline,
                title: 'No saved events yet',
                subtitle: 'Tap the bookmark on an event to save it here',
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (_, i) => _SavedCard(
                item: items[i],
                onTap: () => context.push('/events/${items[i].event.id}'),
                onUnsave: () => _unsave(context, ref, items[i].event.id),
              ),
            );
          },
        ),
      ),
    );
  }

  Future<void> _unsave(
    BuildContext context,
    WidgetRef ref,
    String eventId,
  ) async {
    try {
      await ref.read(eventActionsProvider).unsave(eventId);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(const SnackBar(content: Text('Could not remove')));
      }
    }
  }
}

// ── Card ─────────────────────────────────────────────────────────────────────

class _SavedCard extends StatelessWidget {
  final EventListItem item;
  final VoidCallback onTap;
  final VoidCallback onUnsave;

  const _SavedCard({
    required this.item,
    required this.onTap,
    required this.onUnsave,
  });

  @override
  Widget build(BuildContext context) {
    final event = item.event;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: FromoColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: FromoColors.line),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.32),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            EventThumbnail(imageUrl: event.imageUrl),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
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
                  const SizedBox(height: 3),
                  Text(
                    item.venue.name,
                    style: const TextStyle(
                      fontSize: 12,
                      color: FromoColors.gray500,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      const Icon(
                        Icons.access_time,
                        size: 12,
                        color: FromoColors.gray500,
                      ),
                      const SizedBox(width: 3),
                      Expanded(
                        child: Text(
                          _formatTime(event.startsAt),
                          style: const TextStyle(
                            fontSize: 11,
                            color: FromoColors.gray500,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        event.priceDisplay,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: event.isFree
                              ? FromoColors.gray900
                              : FromoColors.green600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            // Unsave
            IconButton(
              visualDensity: VisualDensity.compact,
              icon: const Icon(Icons.bookmark, color: FromoColors.teal),
              onPressed: onUnsave,
              tooltip: 'Remove',
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final now = DateTime.now();
    final diff = dt.difference(now);
    if (diff.inDays == 0 && dt.day == now.day) return 'Today ${_hm(dt)}';
    final tomorrow = now.add(const Duration(days: 1));
    if (dt.day == tomorrow.day && dt.month == tomorrow.month) {
      return 'Tomorrow ${_hm(dt)}';
    }
    return '${_weekday(dt)} ${_hm(dt)}';
  }

  String _hm(DateTime dt) {
    final h = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
    final m = dt.minute.toString().padLeft(2, '0');
    final period = dt.hour < 12 ? 'AM' : 'PM';
    return '$h:$m $period';
  }

  String _weekday(DateTime dt) {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days[dt.weekday - 1];
  }
}

// ── Empty / error placeholder (scrollable so pull-to-refresh works) ───────────

class _Message extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool scrollable;

  const _Message({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.scrollable = false,
  });

  @override
  Widget build(BuildContext context) {
    final content = Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 56, color: FromoColors.gray200),
          const SizedBox(height: 14),
          Text(
            title,
            style: const TextStyle(color: FromoColors.gray700, fontSize: 15),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            textAlign: TextAlign.center,
            style: const TextStyle(color: FromoColors.gray500, fontSize: 12),
          ),
        ],
      ),
    );

    if (!scrollable) return content;
    return LayoutBuilder(
      builder: (_, constraints) => SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: ConstrainedBox(
          constraints: BoxConstraints(minHeight: constraints.maxHeight),
          child: Padding(padding: const EdgeInsets.all(32), child: content),
        ),
      ),
    );
  }
}
