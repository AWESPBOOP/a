"""Apple Music now playing metadata integration."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

LOGGER = logging.getLogger(__name__)
API_BASE = "https://api.music.apple.com/v1/me/recent/played/tracks"


@dataclass(slots=True)
class AppleMusicTokens:
    developer_token: str
    user_token: Optional[str] = None


@dataclass(slots=True)
class AppleMusicTrack:
    title: str
    artist: str
    album: str
    artwork_url: Optional[str]
    progress_ms: int
    duration_ms: int
    started_at: float


class AppleMusicClient:
    def __init__(self, tokens: AppleMusicTokens, token_store: Path) -> None:
        self._tokens = tokens
        self._token_store = token_store
        self._session = requests.Session()
        self._state_path = token_store
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self.now_playing: Optional[AppleMusicTrack] = None
        self._load_user_token()

    def authenticate(self) -> None:
        if self._tokens.user_token:
            LOGGER.info("Apple Music already authenticated")
            return
        LOGGER.info("Apple Music authentication requires obtaining a MusicKit user token.")
        LOGGER.info("Follow the documentation to generate the token and paste it when prompted.")
        user_token = input("Enter Apple Music user token: ").strip()
        self._tokens.user_token = user_token
        self._state_path.write_text(json.dumps({"user_token": user_token}))
        LOGGER.info("Apple Music user token saved")

    def _load_user_token(self) -> None:
        if self._state_path.exists() and not self._tokens.user_token:
            data = json.loads(self._state_path.read_text())
            self._tokens.user_token = data.get("user_token")

    # ------------------------------------------------------------------
    def fetch_now_playing(self) -> Optional[AppleMusicTrack]:
        if not self._tokens.user_token:
            LOGGER.debug("Apple Music user token missing")
            return None
        headers = {
            "Authorization": f"Bearer {self._tokens.developer_token}",
            "Music-User-Token": self._tokens.user_token,
        }
        response = self._session.get(API_BASE, headers=headers, params={"limit": 1})
        if response.status_code != 200:
            LOGGER.debug("Apple Music request failed: %s", response.text)
            return None
        data = response.json()
        items = data.get("data", [])
        if not items:
            return None
        attrs = items[0]["attributes"]
        duration_ms = int(attrs.get("durationInMillis", 0))
        track = AppleMusicTrack(
            title=attrs.get("name", ""),
            artist=attrs.get("artistName", ""),
            album=attrs.get("albumName", ""),
            artwork_url=attrs.get("artwork", {}).get("url"),
            progress_ms=0,
            duration_ms=duration_ms,
            started_at=time.time(),
        )
        self.now_playing = track
        return track
