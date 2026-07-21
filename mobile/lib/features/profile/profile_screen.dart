import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../core/auth_provider.dart';
import '../../core/constants.dart';
import '../../core/theme.dart';
import '../bookings/bookings_providers.dart';
import '../events/event_detail_providers.dart';
import '../feedback/feedback_prompt.dart';
import '../feedback/feedback_providers.dart';
import '../feedback/feedback_service.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _checkedFeedbackPrompt = false;

  Future<void> _logout(BuildContext context, WidgetRef ref) async {
    await ref.read(authActionsProvider).signOut();
    if (context.mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider);
    final fullName = user?.userMetadata?['full_name'] as String?;
    final displayName = (fullName != null && fullName.trim().isNotEmpty)
        ? fullName.trim()
        : 'Student';
    final savedCount = ref.watch(savedEventsProvider).valueOrNull?.length;
    final bookingCount = ref.watch(myBookingsProvider).valueOrNull?.length;

    if (!_checkedFeedbackPrompt) {
      _checkedFeedbackPrompt = true;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _maybeShowFeedbackPrompt();
      });
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: FromoColors.teal,
              borderRadius: BorderRadius.circular(18),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 34,
                  backgroundColor: Colors.white.withValues(alpha: 0.18),
                  child: Text(
                    displayName.characters.first.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        displayName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        user?.email ?? '',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.82),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _MetricCard(
                  label: 'Saved',
                  value: savedCount?.toString() ?? '-',
                  icon: Icons.bookmark,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _MetricCard(
                  label: 'Bookings',
                  value: bookingCount?.toString() ?? '-',
                  icon: Icons.confirmation_number,
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          _ProfileAction(
            icon: Icons.bookmark_outline,
            title: 'Saved events',
            subtitle: 'Things you want to come back to',
            onTap: () => context.go('/saved'),
          ),
          _ProfileAction(
            icon: Icons.confirmation_number_outlined,
            title: 'My bookings',
            subtitle: 'Confirmed plans and tickets',
            onTap: () => context.go('/bookings'),
          ),
          _ProfileAction(
            icon: Icons.map_outlined,
            title: 'Explore nearby',
            subtitle: 'Return to the live activity map',
            onTap: () => context.go('/map'),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: FromoColors.gray100,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Developer',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: FromoColors.gray900,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'API: ${ApiConfig.baseUrl}',
                  style: const TextStyle(color: FromoColors.gray700),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          OutlinedButton.icon(
            onPressed: () => _logout(context, ref),
            icon: const Icon(Icons.logout),
            label: const Text('Log out'),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size.fromHeight(50),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _maybeShowFeedbackPrompt() async {
    final controller = ref.read(feedbackPromptControllerProvider);
    final shouldPrompt = await controller.shouldPrompt();
    if (!mounted || !shouldPrompt) return;

    await controller.markPromptShown();
    if (!mounted) return;

    final vote = await showAppFeedbackPrompt(context);
    if (!mounted) return;

    if (vote == null) {
      await controller.dismissPrompt();
      return;
    }

    try {
      await controller.submit(vote);
      if (!mounted) return;
      final message = switch (vote) {
        FeedbackVote.up => 'Thanks for the love.',
        FeedbackVote.down => 'Thanks for the honest feedback.',
      };
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(message)));
    } on PostgrestException catch (e) {
      if (!mounted) return;
      final details = e.details;
      final detail =
          (e.message.isNotEmpty ? e.message : null) ??
          (details is String && details.isNotEmpty ? details : null) ??
          'Could not send feedback right now';
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(detail)));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          const SnackBar(content: Text('Could not send feedback right now')),
        );
    }
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: FromoColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: FromoColors.gray200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: FromoColors.teal),
          const SizedBox(height: 12),
          Text(
            value,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: FromoColors.gray900,
            ),
          ),
          Text(label, style: const TextStyle(color: FromoColors.gray500)),
        ],
      ),
    );
  }
}

class _ProfileAction extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _ProfileAction({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: FromoColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: FromoColors.gray200),
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: FromoColors.teal.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: FromoColors.teal),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: FromoColors.gray900,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitle,
                      style: const TextStyle(color: FromoColors.gray500),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: FromoColors.gray500),
            ],
          ),
        ),
      ),
    );
  }
}
