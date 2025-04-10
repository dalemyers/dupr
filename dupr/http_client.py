"""HTTP client for the DUPR API."""

import base64
import datetime
import json
import logging
import os
from platformdirs import user_cache_dir
from typing import Any

import requests

from .auth import DuprAuth, DuprEmailPassword, DuprRefreshToken
from .exceptions import DuprHttpException

TOKENS_PATH = os.path.join(user_cache_dir("dupr"), ".tokens")


class DuprHttpClient:
    """Base class that actually makes API calls to the DUPR API."""

    API_HOST = "https://api.dupr.gg"

    log: logging.Logger
    _username: str
    _password: str
    _access_token: str | None
    _refresh_token: str | None
    _cache_tokens: bool

    _session: requests.Session

    def __init__(
        self,
        *,
        auth: DuprAuth,
        cache_tokens: bool = True,
        log: logging.Logger,
    ) -> None:
        """Construct a new client object."""

        self.log = log.getChild("http")
        self._access_token = None
        self._cache_tokens = cache_tokens

        if isinstance(auth, DuprEmailPassword):
            self._username = auth.email
            self._password = auth.password
            self._refresh_token = None
        elif isinstance(auth, DuprRefreshToken):
            self._refresh_token = auth.refresh_token

        self._session = requests.Session()

    def get_expiry_date(self, token: str) -> int:
        """Get the expiry date of a token.

        :param token: The token to decode

        :returns: The expiry date of the token
        """

        payload_b64 = token.split(".")[1]
        padding_length = 4 - (len(payload_b64) % 4)
        padded_payload_b64 = payload_b64 + ("=" * padding_length)
        payload_bytes = base64.decodebytes(padded_payload_b64.encode("utf-8"))
        payload_string = payload_bytes.decode("utf-8")
        payload = json.loads(payload_string)
        expiration_value = payload["exp"]
        expiration = datetime.datetime.fromtimestamp(expiration_value)
        return expiration

    def refresh_tokens(self) -> tuple[str, str]:
        """Refresh the access token."""

        if self._cache_tokens and os.path.exists(TOKENS_PATH):
            with open(TOKENS_PATH, "r") as f:
                data = json.load(f)

            access_expiry = self.get_expiry_date(data["accessToken"])
            refresh_expiry = self.get_expiry_date(data["refreshToken"])

            if access_expiry > datetime.datetime.now() + datetime.timedelta(minutes=1):
                self._access_token = data["accessToken"]
            else:
                self._access_token = None

            if refresh_expiry > datetime.datetime.now() + datetime.timedelta(minutes=1):
                self._refresh_token = data["refreshToken"]
            else:
                self._refresh_token = None

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

        if self._cache_tokens:
            os.makedirs(os.path.dirname(TOKENS_PATH), exist_ok=True)

            with open(TOKENS_PATH, "w") as f:
                json.dump(data["result"], f)

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
