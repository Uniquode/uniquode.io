# user-profile Specification

## Purpose
TBD - created by archiving change add-user-profile. Update Purpose after archive.
## Requirements
### Requirement: Profile records are owned outside auth
The system SHALL provide a profile capability that stores app-facing user profile records outside the reusable auth schema while linking each profile to an auth user.

#### Scenario: Profile links to auth user
- **WHEN** a profile record is created for an authenticated user
- **THEN** the profile stores a one-to-one reference to the auth user
- **AND** auth-owned tables are not extended with app-facing profile fields

#### Scenario: Profile fields remain app-facing
- **WHEN** additional profile data is added over time
- **THEN** the data is stored through the profile capability
- **AND** reusable auth remains responsible only for identity and account lifecycle concerns

### Requirement: Profile owns profile image descriptors
The system SHALL expose profile image display data through the profile capability so UI consumers can render profile images without depending on auth internals.

#### Scenario: Profile image descriptor is available for UI
- **WHEN** a UI module asks profile for image display data for an auth user
- **THEN** profile returns a descriptor containing renderable image source data or fallback display text
- **AND** the descriptor is owned by profile rather than auth

#### Scenario: Profile image fallback is provided
- **WHEN** a profile has no configured image reference
- **THEN** profile can return fallback display text suitable for an avatar control
- **AND** the fallback does not require profile-image storage to exist

### Requirement: Profile delegates media paths to media capability
The system SHALL delegate profile-picture storage and path resolution to the media capability rather than storing or serving raw filesystem paths inside profile.

#### Scenario: Profile stores media reference
- **WHEN** a profile picture is associated with a user profile
- **THEN** profile stores a media item ID managed by the media capability
- **AND** profile does not store uploaded image binary data in the database

#### Scenario: Profile resolves image source lazily
- **WHEN** profile image source data is required for rendering
- **THEN** profile resolves the stored media item ID through the media capability
- **AND** missing media capability fails through the lazy capability proxy rules rather than module setup ordering

#### Scenario: Profile picture storage key is category structured
- **WHEN** profile creates a storage key for a user profile picture
- **THEN** the storage key uses the `profile` media category
- **AND** the storage key includes deterministic buckets derived from the user ID
- **AND** the original uploaded filename does not control the storage path

#### Scenario: Profile picture upload stores media by ID
- **WHEN** a profile picture upload is accepted for a user
- **THEN** profile derives the profile media storage key
- **AND** delegates the file write and catalogue registration to media
- **AND** stores the returned media item ID on the profile record

