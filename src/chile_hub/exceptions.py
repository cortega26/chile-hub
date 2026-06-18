"""Public exception hierarchy for chile-hub."""


class ChileHubError(Exception):
    """Base class for expected chile-hub runtime errors."""


class ChileHubDataError(ChileHubError, RuntimeError):
    """Raised when release data cannot be resolved or verified."""


class _ChileHubKeyError(ChileHubError, KeyError):
    """KeyError variant with a user-facing string representation."""

    def __str__(self) -> str:
        if not self.args:
            return ""
        return str(self.args[0])


class ChileHubDatasetError(_ChileHubKeyError):
    """Raised when a dataset name is not registered in the catalog."""


class ChileHubOutputError(_ChileHubKeyError):
    """Raised when a dataset output type is not available."""


class ChileHubExampleError(_ChileHubKeyError):
    """Raised when an example kind is not available for a dataset."""
