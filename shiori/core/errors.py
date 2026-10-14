"""Every failure the app can report, each carrying its process exit code."""


class ShioriError(Exception):
    exit_code: int = 1


class UsageError(ShioriError):
    exit_code = 2


class PreflightError(ShioriError):
    exit_code = 3


class ChannelResolveError(ShioriError):
    exit_code = 1


class TabMissingError(ShioriError):
    """A channel tab (e.g. streams) does not exist — skip it, don't fail."""
