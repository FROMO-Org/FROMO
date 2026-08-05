# Mobile References

These sources are real and can be used by the final paper editor for IEEE-style references. They support the mobile methodology, accessibility decisions, Flutter implementation, and mobile web deployment discussion.

## Reference List

[1] Google, "Responsive UI - Material Design." Available: https://m1.material.io/layout/responsive-ui.html

[2] World Wide Web Consortium Web Accessibility Initiative, "Mobile Accessibility at W3C." Available: https://www.w3.org/WAI/standards-guidelines/mobile/

[3] Flutter, "Performance best practices." Available: https://docs.flutter.dev/perf/best-practices

[4] Flutter, "Flutter on the Web." Available: https://docs.flutter.dev/platform-integration/web

[5] Google, "Material Design - Navigation." Available: https://m3.material.io/components/navigation-bar/overview

## Source Summaries

### Google Material Design Responsive UI

Role: Mobile

Type of source: Official design documentation

Key idea: Responsive interfaces should adapt layout and interaction patterns to different screen sizes and device contexts.

How it relates to FROMO: This supports the mobile-first layout decisions, including bottom navigation, compact event cards, map/list combinations, and layout adaptation for smaller screens.

Limitation or gap: It provides general design principles rather than implementation details for this specific event discovery app.

Possible sentence for the literature review: Responsive design principles informed the mobile layout of FROMO, particularly the use of adaptive map and list views for small-screen event discovery.

### W3C Mobile Accessibility

Role: Mobile

Type of source: Official accessibility guideline

Key idea: Mobile applications should consider accessibility needs related to touch interaction, small screens, assistive technologies, and users with disabilities.

How it relates to FROMO: This supports the accessible venue filter and the decision to make accessibility visible in the mobile map interface.

Limitation or gap: It provides broad accessibility guidance rather than a complete implementation model for event discovery and venue routing.

Possible sentence for the literature review: W3C mobile accessibility guidance highlights the importance of inclusive mobile interfaces, which motivated the accessible venue filter in the FROMO mobile map.

### Flutter Performance Best Practices

Role: Mobile

Type of source: Official framework documentation

Key idea: Flutter applications should minimize unnecessary rebuilds, optimize scrolling content, and manage rendering efficiently.

How it relates to FROMO: This supports the use of efficient event lists, reusable widgets, and careful map/list rendering on mobile devices.

Limitation or gap: It focuses on technical performance rather than user experience evaluation.

Possible sentence for the literature review: Flutter performance recommendations guided the implementation of efficient mobile UI components, particularly for event lists and map-based interactions.

### Flutter Web Documentation

Role: Mobile

Type of source: Official framework documentation

Key idea: Flutter supports web deployment for browser-based access, allowing the same application codebase to target mobile and web environments.

How it relates to FROMO: This supports deploying the mobile app as a Netlify-hosted mobile web preview for QR-code access before native app store release.

Limitation or gap: Flutter web behavior can differ from native mobile behavior, especially around browser permissions, payment redirects, and secure storage.

Possible sentence for the methodology: Flutter web deployment allowed the mobile client to be tested through a QR-code-accessible browser version while preserving most of the native mobile user interface.

### Material Design Navigation Bar

Role: Mobile

Type of source: Official design documentation

Key idea: Bottom navigation bars help users move between top-level destinations in mobile applications.

How it relates to FROMO: This supports the FROMO mobile bottom navigation structure: Home, Saved, Bookings, and Profile.

Limitation or gap: It explains navigation patterns but does not evaluate whether the chosen information architecture is optimal for this specific user group.

Possible sentence for the methodology: The mobile app follows common bottom navigation patterns for top-level destinations, making event discovery, saved events, bookings, and profile access available from a consistent navigation bar.
