# Mak Cik Rohani — automated voice demo (real `/chat` UI)

This does **not** use a separate demo page. **Playwright** opens the same **http://localhost:3000/chat** your audience uses, clicks the **real mic button**, and Chromium feeds your clip through a **fake microphone** so **`getUserMedia` → `MediaRecorder` → `/api/transcribe`** runs exactly like a live session (including **waveform**).

## Prerequisites

1. **Frontend:** `npm run dev` (port 3000)
2. **Backend:** FastAPI on the URL in `NEXT_PUBLIC_API_BASE_URL` (usually `http://localhost:8000`)
3. **ffmpeg** (converts your MP3 → WAV; Chromium’s fake mic expects WAV)
   - Windows: `winget install ffmpeg`
   - If `npm run demo:voice-e2e` still says ffmpeg is missing, Node may not see your **User** PATH (common when npm runs from Cursor). Run `cmd /c where ffmpeg`, then either:
     - `set FFMPEG_PATH=C:\full\path\to\ffmpeg.exe` before `npm run demo:voice-e2e`, or  
     - Restart the IDE / add ffmpeg to **System** PATH.
4. **Playwright browser (one-time):**
   ```bash
   npm install
   npx playwright install chromium
   ```

## Audio file

Put **one** of these in place:

- `ElevenLabs_*Mak Cik Rohani*.mp3` in the **repo root**, or  
- `public/demo/mak_cik_rohani.mp3` (e.g. run `.\scripts\copy_rohani_demo_audio.ps1`), or  
- Any path via env: `AUDIO_MP3=C:\path\to\file.mp3`

The script caches a converted WAV under `scripts/demo-cache/` (gitignored).

## Run the E2E script

From the **repo root**:

```bash
npm run demo:voice-e2e
```

### Attach to your existing Chrome (recommended for live demos)

By default the script **launches** its own Chromium and **closes** it when finished. To drive the **same** browser window you already use for `npm run dev` (and leave it open after the voice clip):

**If you see `ECONNREFUSED 127.0.0.1:9222`:** Nothing is listening on the DevTools port. Common causes: (1) you didn’t start the demo Chrome yet; (2) you started Chrome **without** `--remote-debugging-port` while **normal Chrome was already open** — Windows often attaches new launches to the existing process, which **drops** the debug flag. Our helper fixes (2) by using a **separate `--user-data-dir`** (`scripts/chrome-cdp-profile/`, gitignored).

1. **Build the WAV once** (happens automatically on first `npm run demo:voice-e2e`, or run it once so `scripts/demo-cache/mak_cik_rohani_chromium.wav` exists).
2. **Start Chrome with CDP + fake microphone**

   **Windows (easiest — from repo root):**

   ```powershell
   npm run demo:chrome-cdp
   ```

   Use **exactly** that line. Do **not** append Chrome flags after `npm run demo:chrome-cdp` — npm will pass broken arguments to PowerShell (especially if your path has spaces). This script runs `start_chrome_cdp_demo.ps1`, waits until `http://127.0.0.1:9222` responds, then tells you to run attach.

   If the script prints **yellow** (could not confirm CDP), check that port **9222** isn’t used by another app, or pick another port (advanced: change both the `.ps1` and `PLAYWRIGHT_CDP_URL`).

   **Manual (PowerShell — adjust paths):**

   ```powershell
   & "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" `
     '--user-data-dir="C:/Users/YOU/TheInclusiveCitizen/scripts/chrome-cdp-profile"' `
     --remote-debugging-port=9222 `
     --use-fake-device-for-media-stream `
     '--use-file-for-fake-audio-capture="C:/Users/YOU/TheInclusiveCitizen/scripts/demo-cache/mak_cik_rohani_chromium.wav"' `
     "http://localhost:3000/chat"
   ```

   If your Windows profile path has **spaces** (e.g. `Jian Wen Lee`), the path inside each flag **must** be in double quotes or Chrome will open bogus tabs (`http://wen/`, etc.). Prefer `npm run demo:chrome-cdp`, which handles this.

4. In that Chrome window, ensure **`http://localhost:3000/chat`** is open (the script above opens it) and allow mic if prompted.
5. From the repo root:

   ```bash
   npm run demo:voice-e2e:attach
   ```

   Or: `PLAYWRIGHT_CDP_URL=http://127.0.0.1:9222 npm run demo:voice-e2e`  
   Or: `node scripts/e2e-mak-cik-rohani.mjs --cdp-url http://127.0.0.1:9222`

Playwright **connects over CDP**, runs the same mic/stop flow, then **disconnects** — your Chrome **stays open** so you can keep demoing the pipeline manually.

> **Note:** Fake-audio flags must be on the **Chrome process** you attach to; Playwright cannot add them after the fact. If you skip them, the script still clicks the UI but capture may be silent or from a real mic.

Options / env:

| Variable / flag | Meaning |
|-----------------|--------|
| `--cdp` | Attach to `http://127.0.0.1:9222` instead of launching Chromium |
| `--cdp-url <url>` | Custom CDP HTTP endpoint (e.g. another port) |
| `PLAYWRIGHT_CDP_URL` / `CDP_URL` | Same as `--cdp-url` |
| `PERSONA` | `rural` (default), `elderly`, or `migrant` — clicks that persona in the sidebar |
| `RECORD_MS` | Ms to stay “recording” after mic start (**default: length of your MP3 + slack**, via ffprobe) |
| `RECORD_PADDING_MS` | Extra ms after detected length (default `800`; covers mic/UI startup) |
| `--record-seconds N` | Fixed duration in seconds (overrides auto / `RECORD_MS`) |
| `BASE_URL` | Frontend base (default `http://localhost:3000`) |
| `HEADLESS=1` | Headless Chromium (ignored in attach mode; fake mic can be flaky headless) |
| `KEEP_OPEN_MS=60000` | After transcript, wait N ms before closing (**launch mode** only) |
| `NO_BROWSER_CLOSE=1` | After run, do not close Playwright-launched browser (**launch mode** only) |

Example (longer capture, headed, hold window — **launch** mode):

```powershell
$env:PERSONA="rural"
$env:RECORD_MS="12000"
$env:KEEP_OPEN_MS="45000"
npm run demo:voice-e2e
```

## Headless backend-only check

To hit **`/api/transcribe`** without a browser (no UI):

```bash
python scripts/demo_mak_cik_rohani.py
```

## How it works

- Chromium flags: `--use-fake-device-for-media-stream` + `--use-file-for-fake-audio-capture=<absolute path to WAV>`
- The app’s **Mic** / **Stop** controls and **`data-testid="voice-waveform"`** are driven like a user would.
- STT still runs on your **Google Cloud** project; the clip must be long enough and clear enough for your model.
