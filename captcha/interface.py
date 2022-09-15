class CaptchaInterface:
    def get_captcha_result(self, img, target, points_expected=None) -> tuple:
        pass

    def report_error(self, id, error) -> list:
        pass
