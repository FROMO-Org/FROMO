# Mobile Testing Evidence

## Automated Checks

The following checks were run locally from the `mobile` folder.

### Static Analysis

Command:

```bash
flutter analyze
```

Result:

```text
Analyzing mobile...
No issues found! (ran in 2.5s)
```

Note: Flutter printed a non-blocking warning that `flutter_secure_storage` does not yet support Swift Package Manager for iOS. This did not fail analysis.

### Automated Tests

Command:

```bash
flutter test
```

Result:

```text
All tests passed!
```

Observed test coverage included:

- `event_feed_provider_test.dart`: verifies event feed query behavior.
- `bookings_provider_test.dart`: verifies bookings API parsing.
- `feedback_service_test.dart`: verifies feedback prompt timing, cooldown, and payload behavior.
- `widget_test.dart`: app smoke test.
- `feedback_prompt_test.dart`: verifies thumbs-up selection behavior.
- `bookings_screen_test.dart`: verifies empty booking state rendering.
- `map_event_card_test.dart`: verifies event card layout keeps Directions visible on narrow screens.

## Manual Testing Notes

Manual mobile testing was performed using Android emulator devices and mobile web. The following areas were checked during development:

- Map page loads events from the backend.
- Event markers and clustered price pins appear on the map.
- Category filters only show matching future events.
- Accessible filter uses venue accessibility data.
- Event detail page displays image, category, date/time, venue, AI summary, price, and remaining spots.
- Saved events page displays event thumbnails.
- Bookings page displays event thumbnails and booking/payment states.
- Free events allow direct reservation.
- Paid events open Stripe checkout.
- Payment state can show pending or paid depending on backend payment status.
- In-app Directions draws a route, shows distance/time, and provides route controls.
- Mobile web deployment loads from Netlify and connects to the Render backend API.

## Screenshot Evidence

Screenshots captured from the connected Android emulator on 30 July 2026:

- `01_map_clusters.png`: Mobile map showing event price pins, category filters, crowd level labels, and event thumbnail cards.
- `02_event_detail.png`: Event detail page showing event image, category, date/time, venue, AI summary, remaining spots, and Stripe payment button.
- `06_mobile_web.png`: Netlify mobile web deployment opened on the emulator browser. The captured state shows the browser location-permission prompt for `fromomobile.netlify.app`.

The following screenshots still need to be recaptured before final submission:

- `03_in_app_route_needs_recapture.png`: Current emulator interaction did not reliably trigger the in-app route screen during automated screenshot capture.
- `04_saved_events_needs_recapture.png`: Current capture remained on event detail instead of the Saved page.
- `05_bookings_needs_recapture.png`: Current capture remained on event detail instead of the Bookings page.

These pending screenshots should only be used after they are manually verified.
