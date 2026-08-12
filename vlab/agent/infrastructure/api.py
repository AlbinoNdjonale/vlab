from requests import request
from typing import Any, TypedDict

class Response(TypedDict):
    status_code: int
    data: Any

class Api:
    __timeout__ = (3, 15)

    @staticmethod
    def joker(method: str, url: str, data: dict|None = None) -> Response|None:
        try:
            response = request(
                method,
                url,
                data = data,
                timeout = Api.__timeout__
            )

            return {
                'status_code': response.status_code,
                'data': response.json()
            }
        except:
            return None

    @staticmethod
    def get(url: str):
        return Api.joker('GET', url)

    @staticmethod
    def post(url: str, data: dict) -> Response|None:
        return Api.joker('POST', url, data)
