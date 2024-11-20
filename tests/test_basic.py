"""Test base types."""

import base64
import datetime
import json
import os
import sys

from dotenv import load_dotenv
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# pylint: disable=wrong-import-position
import dupr
from dupr.auth import DuprEmailPassword, DuprRefreshToken, DuprAuth

# pylint: enable=wrong-import-position

load_dotenv()


def is_valid_refresh_token(refresh_token: str | None) -> bool:
    """Check if a refresh token is valid."""
    if refresh_token is None:
        return False

    components = refresh_token.split(".")
    if len(components) != 3:
        return False

    body_string = components[1]
    body = base64.b64decode(body_string + "=" * (-len(body_string) % 4))
    body_data = json.loads(body.decode("utf-8"))
    expiry_stamp = body_data.get("exp", 1)
    expiry_date = datetime.datetime.utcfromtimestamp(expiry_stamp)
    now = datetime.datetime.utcnow()

    if expiry_date < now:
        return False

    return True


@pytest.fixture(scope="session", name="client")
def dupr_client() -> dupr.DUPR:
    """Return a DUPR client."""
    if os.path.exists(".refresh_token"):
        with open(".refresh_token", "r", encoding="utf-8") as file:
            refresh_token = file.read()
    else:
        refresh_token = None

    if not is_valid_refresh_token(refresh_token):
        auth: DuprAuth = DuprEmailPassword(
            os.environ["DUPR_EMAIL"], os.environ["DUPR_PASSWORD"]
        )
    else:
        assert refresh_token is not None
        auth = DuprRefreshToken(refresh_token)

    local_client = dupr.DUPR(auth)
    _, refresh_token = local_client.http_client.refresh_tokens()

    with open(".refresh_token", "w", encoding="utf-8") as file:
        file.write(refresh_token)

    return local_client


def test_import():
    """Test that import works."""
    assert dupr is not None


def test_get_user(client: dupr.DUPR):
    """Test that get_user works."""
    members = list(client.get_club_members(8144440321))
    assert len(members) > 0


def test_search_players(client: dupr.DUPR):
    """Test that search_players works."""
    players = list(client.search_players("8144440321"))
    assert len(players) > 0


def test_get_player(client: dupr.DUPR):
    """Test that get_player works."""
    player = list(client.get_player(4981843663))
    assert player is not None
