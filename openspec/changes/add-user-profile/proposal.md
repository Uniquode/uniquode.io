## Why

Linear: [UT-222](https://linear.app/uniquode/issue/UT-222/add-user-profile)

Reusable Wevra auth should stay focused on authentication, account state, and
identity lifecycle. The application needs app-owned profile data, such as a
profile picture reference, with a different ownership model and storage policy
from reusable auth.

Profile media also needs an explicit writable storage root so uploads resolve
consistently across local development and deployment instead of relying on
ad-hoc filesystem paths.

## What Changes

- Add an app-owned user profile table linked one-to-one with auth users.
- Store additional app-managed user information outside the Wevra auth schema.
- Add an initial profile picture path/reference field for user profile images.
- Store media references as paths relative to the configured media root where
  practical, rather than storing uploaded image binary data in the database.
- Add `[app.media].path` to application configuration as the writable media
  storage root for profile pictures and related user-uploaded media.
- Resolve relative media paths consistently with the loaded application
  configuration/project root.
- Validate media path existence and writability before workflows that need
  uploads use it.
- Leave room for future app profile fields without adding them to reusable auth
  tables or overfitting the initial schema.
- Defer a public media/CDN serving strategy until product requirements need it.

## Capabilities

### New Capabilities

- `user-profile`: Application-owned user profile persistence, auth-user
  linkage, profile-picture reference storage, and profile lifecycle policy.
- `media-storage`: Application media-root configuration, path resolution, and
  writable storage expectations for user-uploaded media.

### Modified Capabilities

- `environment-configuration`: Add `[app.media].path` to supported application
  configuration and validation behaviour.

## Impact

- Affects app models, migrations, settings, configuration examples,
  validation, profile-related services, and future profile routes/templates.
- Keeps Wevra auth reusable by linking to auth users rather than extending
  auth-owned tables.
- Adds no new runtime dependency unless later design work identifies a concrete
  image-processing or storage requirement.
