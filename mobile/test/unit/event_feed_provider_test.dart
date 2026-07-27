import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fromo/core/api_client.dart';
import 'package:fromo/features/map/map_providers.dart';
import 'package:latlong2/latlong.dart';

import '../mocks/mock_api_client.dart';

void main() {
  test('all-events feed matches web query rules', () async {
    Map<String, dynamic>? capturedParams;
    final api = FakeApiClient(
      onGet: (path, params) async {
        expect(path, '/events/');
        capturedParams = params;
        return Response<dynamic>(
          requestOptions: RequestOptions(path: path),
          data: <dynamic>[],
          statusCode: 200,
        );
      },
    );
    final container = ProviderContainer(
      overrides: [apiClientProvider.overrideWithValue(api)],
    );
    addTearDown(container.dispose);

    await container.read(eventFeedProvider(EventFeedScope.all).future);

    expect(capturedParams?['status'], 'active');
    expect(capturedParams?['limit'], 30);
    expect(capturedParams?['starts_after'], isNotNull);
    expect(
      DateTime.parse(capturedParams!['starts_after'] as String).isUtc,
      isTrue,
    );
    expect(capturedParams, isNot(contains('lat')));
    expect(capturedParams, isNot(contains('lng')));
    expect(capturedParams, isNot(contains('radius_km')));
  });

  test('nearby feed matches web one-kilometre query rules', () async {
    Map<String, dynamic>? capturedParams;
    final api = FakeApiClient(
      onGet: (path, params) async {
        expect(path, '/events/');
        capturedParams = params;
        return Response<dynamic>(
          requestOptions: RequestOptions(path: path),
          data: <dynamic>[],
          statusCode: 200,
        );
      },
    );
    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(api),
        locationProvider.overrideWith(
          (ref) => _LocatedNotifier(const LatLng(53.3498, -6.2603)),
        ),
      ],
    );
    addTearDown(container.dispose);

    await container.read(eventFeedProvider(EventFeedScope.nearby).future);

    expect(capturedParams?['status'], 'active');
    expect(capturedParams?['limit'], 30);
    expect(capturedParams?['lat'], 53.3498);
    expect(capturedParams?['lng'], -6.2603);
    expect(capturedParams?['radius_km'], 1);
    expect(capturedParams, isNot(contains('starts_after')));
  });
}

class _LocatedNotifier extends LocationNotifier {
  _LocatedNotifier(LatLng position) {
    state = LocationState(position: position);
  }
}
