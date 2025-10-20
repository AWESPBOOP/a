# Spotify & Apple Music OAuth Setup

NebulaVis supports metadata sync from Spotify and Apple Music. Audio analysis still relies on local capture; metadata provides artwork, track titles, tempo hints, and playback position.

## Spotify

1. Create a Spotify developer application at <https://developer.spotify.com/dashboard>.
2. Add `http://localhost:43919/callback` to the **Redirect URIs**.
3. Copy the **Client ID**.
4. Set the environment variable before launching NebulaVis:

   ```bash
   export NEBULAVIS_SPOTIFY_CLIENT_ID="your-client-id"
   uv run nebulavis run
   ```

5. From the dashboard click **Login Spotify**. A browser window will ask for permission. After accepting, the CLI prints *Spotify authentication complete*.

The OAuth tokens are stored in `~/.config/nebulavis/spotify.json`.

## Apple Music

1. Generate an Apple Music developer token using MusicKit (see Apple's documentation). Store it securely.
2. Set the environment variable:

   ```bash
   export NEBULAVIS_APPLE_DEVELOPER_TOKEN="your-developer-token"
   ```

3. Run NebulaVis and click **Login Apple Music**. Paste the user token when prompted. The token persists in `~/.config/nebulavis/apple_music.json`.

Apple Music only exposes metadata, so NebulaVis uses your local analysis for beat detection. The timestamp is reconciled against the server clock to keep drift below ±150 ms.
