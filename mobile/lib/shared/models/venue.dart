class Venue {
  final String id;
  final String name;
  final String? address;
  final double lat;
  final double lng;
  final String? category;
  final bool isAccessible;

  const Venue({
    required this.id,
    required this.name,
    this.address,
    required this.lat,
    required this.lng,
    this.category,
    required this.isAccessible,
  });

  factory Venue.fromJson(Map<String, dynamic> j) => Venue(
        id: j['id'] as String,
        name: j['name'] as String,
        address: j['address'] as String?,
        lat: (j['lat'] as num).toDouble(),
        lng: (j['lng'] as num).toDouble(),
        category: j['category'] as String?,
        isAccessible: j['is_accessible'] as bool? ?? false,
      );
}
