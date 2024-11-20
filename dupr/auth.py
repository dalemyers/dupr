"""DUPR API exceptions."""

import abc


class DuprAuth(abc.ABC):
    """All DUPR Auth inherits from this."""


class DuprEmailPassword(DuprAuth):
    """DUPR auth using email and password."""

    email: str
    password: str

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password


class DuprRefreshToken(DuprAuth):
    """DUPR auth using a refresh token."""

    refresh_token: str

    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
