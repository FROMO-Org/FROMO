# Mobile Test Plan

This document outlines the recommended testing strategy for the Flutter mobile app.

## Goals

- Catch regressions in app logic early
- Protect critical user flows such as login, browsing events, saving, booking, and feedback
- Reduce reliance on live backend and Supabase during development
- Add enough UI coverage to prevent accidental layout and state regressions

## Test Categories

### 1. Unit Tests

Focus on pure logic, parsing, formatting, and state rules.

Recommended coverage:

- `Event.fromJson`, `Venue.fromJson`, `BookingListItem.fromJson`
- `Event.priceDisplay`
- `Event.originalPriceDisplay`
- `Event.isPast`
- feedback prompt cooldown rules
- booking state and status helpers

Why this matters:

- Fastest tests to run
- Cheapest tests to maintain
- Best place to lock down business logic

### 2. Component Tests

Use Flutter widget tests for isolated UI pieces and local interactions.

Recommended coverage:

- feedback prompt renders correctly
- feedback prompt returns `thumbs up`
- feedback prompt returns `thumbs down`
- feedback prompt dismisses on `Maybe later`
- booking button states: idle, loading, booked
- event detail page loading, error, and success UI
- profile screen action cards render correctly

Why this matters:

- Catches UI regressions without running the full app
- Good balance of speed and confidence

### 3. Integration Tests

Use `integration_test` for core flows across screens and providers.

Recommended coverage:

- sign in flow
- open map and load nearby events
- open event detail from list/map
- save and unsave an event
- booking success flow
- booking error flow
- feedback prompt appears under the right conditions

Why this matters:

- Verifies screens, routing, providers, and async actions work together

### 4. End-to-End Tests

Keep this small and focused on the highest-value real-user journeys.

Recommended coverage:

- new user signs in and browses events
- existing user saves an event and books it
- paid booking flow after payment is implemented

Why this matters:

- Highest realism
- Highest maintenance cost
- Should be limited to only a few important journeys

### 5. Visual and Responsive Tests

Add visual regression coverage for key screens and important device sizes.

Recommended coverage:

- map screen
- event detail screen
- profile screen
- feedback bottom sheet
- small phone layout
- large phone layout
- tablet-width layout if supported

Suggested approach:

- golden tests for stable widgets/screens
- check that text does not overflow
- check bottom sheets and action bars remain visible

Why this matters:

- Helps prevent layout breakage from UI edits

### 6. API Mocking Tests

Mock backend and Supabase dependencies so tests remain stable and deterministic.

Recommended coverage:

- mock `ApiClient` success and failure cases
- mock Supabase logged-in user/session
- mock feedback insert success/failure
- mock events list responses
- mock bookings responses
- mock saved-events responses

Why this matters:

- Lets mobile tests run without live services
- Makes edge-case testing much easier

## Recommended Priority

### Phase 1

Status: implemented as the current baseline.

Build the foundation first:

- Unit Tests
- Component Tests
- API Mocking Tests

### Phase 2

Status: implemented as a lightweight integration baseline.

Add cross-screen confidence:

- Integration Tests

### Phase 3

Add polish and regression protection:

- Visual and Responsive Tests
- Small number of End-to-End Tests

## First 8 Tests To Implement

1. Done: `Event.fromJson` parses `url`, `ai_summary`, time fields, and price fields correctly
2. Done: `Event.isPast` behaves correctly with and without `endsAt`
3. Done: feedback prompt does not appear again within 30 days after successful submission
4. Done: feedback prompt does not appear again within 7 days after dismissal
5. Done: feedback prompt returns the correct result for `thumbs up`
6. Done: `EventDetailScreen` shows the error state when the detail provider fails
7. Done: `BookingsScreen` shows the empty state when there are no bookings
8. Done: mocked booking provider parses API data without a live backend

## Implemented Baseline

Phase 1 currently includes:

- `test/unit/event_model_test.dart`
- `test/unit/feedback_service_test.dart`
- `test/unit/bookings_provider_test.dart`
- `test/widgets/feedback_prompt_test.dart`
- `test/widgets/bookings_screen_test.dart`
- `test/widgets/event_detail_screen_test.dart`
- `test/mocks/mock_api_client.dart`

Phase 2 currently includes:

- `integration_test/core_flows_test.dart`

## Suggested File Structure

```text
mobile/
├── test/
│   ├── unit/
│   ├── widgets/
│   ├── mocks/
│   └── golden/
├── integration_test/
│   └── app_flows_test.dart
└── TEST_PLAN.md
```

## Suggested Initial Test Files

```text
test/unit/event_model_test.dart
test/unit/feedback_service_test.dart
test/widgets/feedback_prompt_test.dart
test/widgets/event_detail_screen_test.dart
test/widgets/bookings_screen_test.dart
test/mocks/mock_api_client.dart
integration_test/core_flows_test.dart
```

## Implementation Notes

- Prefer mocking providers and services instead of hitting real backend endpoints
- Keep unit tests focused on business rules, not widget trees
- Keep widget tests focused on rendering and local interaction
- Keep integration tests focused on a few complete user flows
- Only add golden tests for screens that are visually stable enough to maintain

## Definition of Done

The mobile app testing baseline is considered in place when:

- core model logic has unit coverage
- feedback flow has unit and widget coverage
- booking and event detail screens have widget coverage
- at least one integration test covers a main user journey
- tests can run locally without requiring a live backend for most cases
