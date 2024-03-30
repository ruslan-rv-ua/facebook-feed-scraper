class FBBrowserError(Exception):
    pass


class BrowserAlreadyRunningException(FBBrowserError):
    pass


class BrowserNotRunningException(FBBrowserError):
    pass
