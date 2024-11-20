"""A DUPR API Wrapper."""

import logging
from typing import Any, Iterator

from .http_client import DuprHttpClient
from .auth import DuprAuth, DuprEmailPassword, DuprRefreshToken


class DUPR:
    """A DUPR API Wrapper."""

    log: logging.Logger
    http_client: DuprHttpClient
    _is_logged_in: bool

    def __init__(
        self,
        auth: DuprAuth,
        *,
        log: logging.Logger | None = None,
    ):
        if log is None:
            self.log = logging.getLogger("dupr")
        else:
            self.log = log.getChild("dupr")

        self._is_logged_in = False

        self.http_client = DuprHttpClient(auth=auth, log=self.log)

    def get_club_members(self, club_id: int) -> Iterator[dict[str, Any]]:
        """Get all members of a club.

        :param club_id: The ID of the club

        :return: An iterator of all members
        """
        offset = 0
        limit = 25  # 25 is the max allowed by the API

        while True:
            body = {
                "offset": offset,
                "limit": limit,
                "query": "*",
            }
            response = self.http_client.post(
                f"/club/{club_id}/members/v1.0/all", json_data=body
            )
            data = response.json()
            hits = data["result"]["hits"]
            if len(hits) == 0:
                break
            yield from hits
            offset += limit
