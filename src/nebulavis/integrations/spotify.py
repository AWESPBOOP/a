"""Spotify Web API integration for NebulaVis."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import string
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import requests

LOGGER = logging.getLogger(__name__)

AUTH_BASE = "https://accounts.spotify.com"
API_BASE = "https://api.spotify.com/v1"
REDIRECT_URI = "http://localhost:43919/callback"
SCOPES = "user-read-currently-playing user-read-playback-state"


@dataclass(slots=True)
class TrackMetadata:
    title: str
    artist: str
    album: str
    album_art_url: str | None
    tempo: float | None
    progress_ms: int
    duration_ms: int
    started_at: float
    device_name: str | None = None
    palette: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SpotifyState:
    now_playing: Optional[TrackMetadata] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: float = 0.0


class TokenStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> SpotifyState:
        if not self._path.exists():
            return SpotifyState()
        data = json.loads(self._path.read_text())
        return SpotifyState(**data)

    def save(self, state: SpotifyState) -> None:
        payload = {
            "access_token": state.access_token,
            "refresh_token": state.refresh_token,
            "expires_at": state.expires_at,
        }
        self._path.write_text(json.dumps(payload, indent=2))


class SpotifyClient:
    def __init__(self, client_id: str, token_store: TokenStore) -> None:
        self._client_id = client_id
        self._token_store = token_store
        self.state = token_store.load()
        self._session = requests.Session()
        self.preset_manager = None

    # ------------------------------------------------------------------
    def authenticate(self) -> None:
        LOGGER.info("Starting Spotify OAuth flow")
        verifier = self._code_verifier()
        challenge = self._code_challenge(verifier)
        url = (
            f"{AUTH_BASE}/authorize?response_type=code&client_id={self._client_id}" f"&redirect_uri={REDIRECT_URI}&code_challenge_method=S256"
            f"&code_challenge={challenge}&scope={SCOPES.replace(' ', '%20')}"
        )
        LOGGER.info("Open the following URL in your browser to authorize: %s", url)
        code = self._await_callback()
        if not code:
            LOGGER.error("Authorization failed: no code received")
            return
        token_data = self._exchange_token(code, verifier)
        self.state.access_token = token_data["access_token"]
        self.state.refresh_token = token_data.get("refresh_token")
        self.state.expires_at = time.time() + token_data["expires_in"]
        self._token_store.save(self.state)
        LOGGER.info("Spotify authentication complete")

    def _await_callback(self) -> Optional[str]:  # pragma: no cover - networking
        from http.server import BaseHTTPRequestHandler, HTTPServer
        code_container: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # type: ignore[override]
                from urllib.parse import parse_qs, urlparse

                params = parse_qs(urlparse(self.path).query)
                code = params.get("code", [None])[0]
                code_container["code"] = code or ""
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Authorization received. You can close this window.")

            def log_message(self, format, *args):  # noqa: A003 - silence http server
                return

        server = HTTPServer(("", 43919), Handler)
        LOGGER.info("Waiting for Spotify authorization callback...")
        server.handle_request()
        server.server_close()
        return code_container.get("code")

    def _exchange_token(self, code: str, verifier: str) -> dict[str, Any]:
        response = self._session.post(
            f"{AUTH_BASE}/api/token",
            data={
                "client_id": self._client_id,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": verifier,
            },
        )
        response.raise_for_status()
        return response.json()

    def refresh_token(self) -> None:
        if not self.state.refresh_token:
            raise RuntimeError("No refresh token available")
        response = self._session.post(
            f"{AUTH_BASE}/api/token",
            data={
                "client_id": self._client_id,
                "grant_type": "refresh_token",
                "refresh_token": self.state.refresh_token,
            },
        )
        response.raise_for_status()
        data = response.json()
        self.state.access_token = data["access_token"]
        self.state.expires_at = time.time() + data["expires_in"]
        self._token_store.save(self.state)

    # ------------------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        if not self.state.access_token:
            raise RuntimeError("Spotify not authenticated")
        if time.time() >= self.state.expires_at - 30 and self.state.refresh_token:
            self.refresh_token()
        return {"Authorization": f"Bearer {self.state.access_token}"}

    def fetch_current_track(self) -> Optional[TrackMetadata]:
        response = self._session.get(f"{API_BASE}/me/player/currently-playing", headers=self._headers())
        if response.status_code == 204:
            return None
        response.raise_for_status()
        data = response.json()
        if not data.get("item"):
            return None
        item = data["item"]
        artists = ", ".join(artist["name"] for artist in item["artists"])
        album = item["album"]["name"]
        artwork = None
        if item["album"].get("images"):
            artwork = item["album"]["images"][0]["url"]
        tempo = self._fetch_tempo(item["id"])
        progress = data.get("progress_ms", 0)
        duration = item.get("duration_ms", 0)
        started_at = time.time() - progress / 1000.0
        device_name = data.get("device", {}).get("name")
        metadata = TrackMetadata(
            title=item["name"],
            artist=artists,
            album=album,
            album_art_url=artwork,
            tempo=tempo,
            progress_ms=progress,
            duration_ms=duration,
            started_at=started_at,
            device_name=device_name,
        )
        self.state.now_playing = metadata
        return metadata

    def _fetch_tempo(self, track_id: str) -> Optional[float]:
        response = self._session.get(f"{API_BASE}/audio-features/{track_id}", headers=self._headers())
        if response.status_code != 200:
            LOGGER.debug("Audio features unavailable: %s", response.text)
            return None
        data = response.json()
        return data.get("tempo")

    # ------------------------------------------------------------------
    def _code_verifier(self) -> str:
        alphabet = string.ascii_letters + string.digits + "-._~"
        return "".join(secrets.choice(alphabet) for _ in range(64))

    def _code_challenge(self, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")
