# LocalTube  — localhost YouTube downloader

This version includes a workaround for the recent YouTube `tv_downgraded` / "The page needs to be reloaded" extraction problem and updates yt-dlp to the current stable release.

## Windows setup

**1. Use Python 3.11+** (recommended by current yt-dlp releases).

**2. Install FFmpeg** and make sure `ffmpeg.exe` is available from PowerShell:
```powershell
ffmpeg -version
```

**3. Open PowerShell in this folder:**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**4. Start the app:**
```powershell
python app.py
```

Open:
http://127.0.0.1:5000

### If YouTube still says "The page needs to be reloaded"

First update:
```powershell
pip install -U "yt-dlp[default]"
```

The current yt-dlp release is 2026.08.19. Recent YouTube extraction changes can temporarily break some videos/clients.

If the error is specifically about JavaScript challenges, install a supported JS runtime such as Deno and restart the terminal. Current yt-dlp releases use the EJS challenge-solving components, but a supported runtime is still needed for some YouTube extraction paths.

### Important
Some videos can still be unavailable because of age restrictions, region restrictions, private status, embedding restrictions, sign-in requirements, or YouTube-side anti-bot changes. The app cannot override those restrictions.

Only download content you have permission to download and comply with YouTube's terms and copyright law.

## v3 UI
This release adds a dashboard-style sidebar, polished dark/blue interface, download card, and MB-based transfer display with ETA shown to one decimal place.
