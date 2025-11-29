import requests
import io

from aiogram.types import FSInputFile


class TelegramAPI:
    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token

    def sendRequest(self, request_method: str, api_method: str, parameters: dict = {}, files: dict = None) -> dict:
        """
        Sends request to Telegram API.

        :param request_method: http request method (`get` or `post`).
        :param api_method: the required method in Telegram API.
        :param parameters: dict of parameters which will used in the Telegram API method.
        :param files: dict of files to upload (for multipart/form-data).
        """

        url = f"https://api.telegram.org/bot{self.bot_token}/{api_method}"
        
        if files:
            files_dict = {}
            for key, file_input in files.items():
                if isinstance(file_input, FSInputFile):
                    files_dict[key] = (file_input.filename, open(file_input.path, 'rb'))
                else:
                    files_dict[key] = file_input
            
            match request_method:
                case "GET":
                    r = requests.get(url, params=parameters, files=files_dict)
                case "POST":
                    r = requests.post(url, data=parameters, files=files_dict)
            
            for key, file_tuple in files_dict.items():
                file_obj = file_tuple[1]
                if hasattr(file_obj, 'close') and callable(file_obj.close):
                    file_obj.close()
        else:
            parameters_string = "&".join([f"{k}={v}" for k, v in parameters.items()])
            request_url = f"{url}?{parameters_string}"

            match request_method:
                case "GET":
                    r = requests.get(request_url)
                case "POST":
                    r = requests.post(request_url)

        response = {
            "code": r.status_code,
            "text": r.text,
        }
        
        return response
