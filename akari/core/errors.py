"""Every failure the app can report, each carrying its process exit code."""


class AkariError(Exception):
    exit_code: int = 1


class UsageError(AkariError):
    exit_code = 2


class PreflightError(AkariError):
    exit_code = 3


class ChannelResolveError(AkariError):
    exit_code = 1
