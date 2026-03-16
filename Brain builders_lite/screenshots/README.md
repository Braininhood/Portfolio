# Screenshots

This folder contains screenshots from automated testing of the Brain Bulders MVP.

## Folder Structure

### `/unauthenticated/`
Screenshots from testing public pages (no login required):
- Homepage
- Mentor browsing
- Public profiles
- Navigation
- Landing pages

### `/authenticated/`
Screenshots from testing logged-in user features:
- Dashboard
- Profile pages
- Settings
- User-specific features
- Mentor dashboard

### `/features/`
Screenshots demonstrating specific features:
- Booking flow
- Product purchases
- Chat/messaging
- Video responses
- AI recommendations
- Time scheduling

### `/errors/`
Screenshots capturing errors and issues:
- Failed operations
- Error messages
- Console errors
- Broken features
- 404 pages

## Usage

### Manual Screenshots
When manually testing features, save screenshots to the appropriate subfolder:
```
screenshots/
├── authenticated/feature-name-description.png
├── features/booking-flow-step1.png
└── errors/login-error-message.png
```

### Automated Test Screenshots
Test scripts should be configured to save screenshots to these folders:
```javascript
await page.screenshot({ 
  path: 'screenshots/authenticated/dashboard.png' 
});
```

## Naming Convention

Use descriptive names with hyphens:
- `homepage-desktop-view.png`
- `mentor-profile-ted-jones.png`
- `booking-calendar-selection.png`
- `error-payment-failed.png`

Include dates for version tracking if needed:
- `dashboard-2026-02-20.png`

## Archive

Historical screenshots from previous test runs are stored in:
- `../screenshots-archive/` - Organized by test run date/type

## Best Practices

1. **Be descriptive** - Name clearly describes what's shown
2. **Use subfolders** - Keep organized by category
3. **Include context** - Capture enough of the page to understand context
4. **Document errors** - Always screenshot error states
5. **Timestamp important changes** - For tracking evolution of features

## File Formats

- Use PNG for UI screenshots (lossless, good for text)
- Keep reasonable resolution (1920x1080 max for most cases)
- Compress large files if needed

## Gitignore

This folder is included in `.gitignore` to avoid committing large binary files. 
Screenshots are for local testing reference only.
