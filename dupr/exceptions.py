"""DUPR API exceptions."""

import requests


class DuprException(Exception):
    """All DUPR exceptions inherit from this or instantiate it."""


class DuprHttpException(DuprException):
    """All DUPR HTTP exceptions use this class.

    :param message: The message for the exception
    :param response: The response to the HTTP request
    """

    message: str
    response: requests.Response

    def __init__(self, message: str, response: requests.Response) -> None:
        super().__init__()
        self.message = message
        self.response = response

    def __str__(self) -> str:
        """Generate and return the string representation of the object.

        :return: A string representation of the object
        """
        return f"{self.message}, status_code={self.response.status_code}, text={self.response.text}"
