class CaptchaRequestError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class CaptchaBusinessError(CaptchaRequestError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class CaptchaResultError(CaptchaRequestError):
    def __init__(self, *args: object, **kwargs) -> None:
        self.id = kwargs.get("id")
        super().__init__(*args)
