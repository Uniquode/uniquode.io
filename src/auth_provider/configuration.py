"""Configuration errors for the auth provider package."""


class ProviderConfigurationError(ValueError):
    """Raised when immutable OAuth provider options are invalid.

    Runtime provider workflows should prefer explicit result values for
    expected failure states; this exception is reserved for construction-time
    configuration that cannot produce a usable options object.
    """
