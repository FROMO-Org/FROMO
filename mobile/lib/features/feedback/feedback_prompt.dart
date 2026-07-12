import 'package:flutter/material.dart';

import '../../core/theme.dart';
import 'feedback_service.dart';

Future<FeedbackVote?> showAppFeedbackPrompt(BuildContext context) {
  return showModalBottomSheet<FeedbackVote>(
    context: context,
    showDragHandle: true,
    backgroundColor: Colors.white,
    builder: (_) => const _FeedbackPromptSheet(),
  );
}

class _FeedbackPromptSheet extends StatelessWidget {
  const _FeedbackPromptSheet();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'How is FROMO feeling so far?',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: FromoColors.gray900,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'A quick thumbs up or down helps us improve the app experience.',
              style: TextStyle(
                fontSize: 14,
                height: 1.5,
                color: FromoColors.gray500,
              ),
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: _VoteButton(
                    icon: Icons.thumb_up_alt_outlined,
                    label: 'Thumbs up',
                    color: FromoColors.green600,
                    onTap: () {
                      Navigator.of(context).pop(FeedbackVote.up);
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _VoteButton(
                    icon: Icons.thumb_down_alt_outlined,
                    label: 'Thumbs down',
                    color: const Color(0xFFDC2626),
                    onTap: () {
                      Navigator.of(context).pop(FeedbackVote.down);
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Maybe later'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VoteButton extends StatelessWidget {
  const _VoteButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Ink(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withValues(alpha: 0.22)),
          color: color.withValues(alpha: 0.06),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 28, color: color),
            const SizedBox(height: 10),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
