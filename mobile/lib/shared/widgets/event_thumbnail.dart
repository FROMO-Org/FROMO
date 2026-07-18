import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../../core/theme.dart';

class EventThumbnail extends StatelessWidget {
  final String? imageUrl;
  final double size;
  final double borderRadius;
  final double iconSize;

  const EventThumbnail({
    super.key,
    required this.imageUrl,
    this.size = 72,
    this.borderRadius = 12,
    this.iconSize = 30,
  });

  @override
  Widget build(BuildContext context) {
    final normalizedUrl = imageUrl?.trim();

    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: normalizedUrl == null || normalizedUrl.isEmpty
          ? _EventThumbnailPlaceholder(size: size, iconSize: iconSize)
          : CachedNetworkImage(
              imageUrl: normalizedUrl,
              width: size,
              height: size,
              fit: BoxFit.cover,
              placeholder: (_, _) =>
                  _EventThumbnailPlaceholder(size: size, iconSize: iconSize),
              errorWidget: (_, _, _) =>
                  _EventThumbnailPlaceholder(size: size, iconSize: iconSize),
            ),
    );
  }
}

class _EventThumbnailPlaceholder extends StatelessWidget {
  final double size;
  final double iconSize;

  const _EventThumbnailPlaceholder({
    required this.size,
    required this.iconSize,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      color: FromoColors.gray100,
      child: Icon(Icons.event, color: FromoColors.gray500, size: iconSize),
    );
  }
}
