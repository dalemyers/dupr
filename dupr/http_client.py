"""HTTP client for the DUPR API."""

import logging
from typing import Any

import requests

from .auth import DuprAuth, DuprEmailPassword, DuprRefreshToken
from .exceptions import DuprHttpException


class DuprHttpClient:
    """Base class that actually makes API calls to the DUPR API."""

    API_HOST = "https://api.dupr.gg"

    log: logging.Logger
    _username: str
    _password: str
    _access_token: str | None
    _refresh_token: str | None

    _session: requests.Session

    def __init__(
        self,
        *,
        auth: DuprAuth,
        log: logging.Logger,
    ) -> None:
        """Construct a new client object."""

        self.log = log.getChild("http")
        self._access_token = None

        if isinstance(auth, DuprEmailPassword):
            self._username = auth.email
            self._password = auth.password
            self._refresh_token = None
        elif isinstance(auth, DuprRefreshToken):
            self._refresh_token = auth.refresh_token

        self._session = requests.Session()

    def refresh_tokens(self) -> tuple[str, str]:
        """Refresh the access token."""

        if self._access_token and self._refresh_token:
            return (self._access_token, self._refresh_token)

        if self._refresh_token:
            response = self._session.get(
                DuprHttpClient.API_HOST + "/auth/v1.0/refresh",
                headers={"x-refresh-token": self._refresh_token},
            )

            data = response.json()
            self._access_token = data["result"]

            assert self._access_token
            assert self._refresh_token

            return (self._access_token, self._refresh_token)

        response = self._session.post(
            DuprHttpClient.API_HOST + "/auth/v1.0/login",
            json={"email": self._username, "password": self._password},
        )

        if response.status_code != 200:
            raise DuprHttpException("Failed to authenticate", response)

        data = response.json()
        self._access_token = data["result"]["accessToken"]
        self._refresh_token = data["result"]["refreshToken"]

        assert self._access_token
        assert self._refresh_token

        return (self._access_token, self._refresh_token)

    def get(
        self,
        request_path: str,
    ) -> requests.Response:
        """Issue a GET request with the correct headers.

        :param request_path: The URL path to issue the request to

        :returns: The raw response object from the API
        """

        self.refresh_tokens()

        response = self._session.get(
            DuprHttpClient.API_HOST + request_path,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )

        if response.status_code == 429:
            print()

        return response

    def post(
        self,
        request_path: str,
        *,
        json_data: Any | None = None,
    ) -> requests.Response:
        """Issue a POST request with the correct  headers.

        Note: If `json_data` and `operations` are not None, the latter will take
        precedence.

        :param request_path: The URL path to issue the request to
        :param json_data: The JSON data to send with the request

        :returns: The raw response object from the API
        """

        self.refresh_tokens()

        return self._session.post(
            DuprHttpClient.API_HOST + request_path,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
            },
            json=json_data,
        )
