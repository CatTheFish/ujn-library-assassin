class LeoLibWebRequestError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class LeoLibWebAuthenticationError(LeoLibWebRequestError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class LeoLibWebCaptchaError(LeoLibWebRequestError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class LeoLibWebSeatUnavailableError(LeoLibWebRequestError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class LeoLibWebBookingUnavailableError(LeoLibWebRequestError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
