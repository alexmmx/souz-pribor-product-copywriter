"""Stable application errors for user-facing boundaries."""


class ProductCopywriterError(Exception):
    """Base class for expected application failures."""


class InputFileError(ProductCopywriterError):
    """The input file could not be read."""


class InputValidationError(ProductCopywriterError):
    """The input JSON does not match the product contract."""


class ConfigurationError(ProductCopywriterError):
    """Required local configuration is absent or invalid."""


class ProviderError(ProductCopywriterError):
    """The configured LLM provider could not produce a usable response."""


class GroundingError(ProductCopywriterError):
    """Generated copy contains a value that is not grounded in the input."""
