import requests


class TelegramAPI:
    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token

    def sendRequest(self, request_method: str, api_method: str, parameters: dict = {}) -> dict:
        """
        Sends request to Telegram API.

        :param request_method: http request method (`get` or `post`).
        :param api_method: the required method in Telegram API.
        :param parameters: dict of parameters which will used in the Telegram API method.
        """

        parameters_string = "&".join([f"{k}={v}" for k, v in parameters.items()])

        request = f"https://api.telegram.org/bot{self.bot_token}/{api_method}?{parameters_string}"

        match request_method:
            case "GET":
                r = requests.get(request)
            case "POST":
                r = requests.post(request)

        response = {
            "code": r.status_code,
            "text": r.text,
        }
        
        return response
