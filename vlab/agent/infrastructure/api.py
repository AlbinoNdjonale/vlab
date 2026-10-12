from requests import request
from typing import Any, TypedDict

class Response(TypedDict):
    status_code: int
    data: Any

class Api:
    __timeout__ = (3, 15)

    @staticmethod
    def joker(method: str, url: str, data = None) -> Response|None:
        try:
            response = request(
                method,
                url,
                data = data,
                timeout = Api.__timeout__
            )

            try:
                data = response.json()
            except:
                data = {}

            return {
                'status_code': response.status_code,
                'data': data
            }
        except:
            return None

    @staticmethod
    def get(url: str):
        return Api.joker('GET', url)

    @staticmethod
    def post(url: str, data) -> Response|None:
        return Api.joker('POST', url, data)
