#!/usr/bin/env node
/**
 * E2E demo: drives the REAL /chat UI — mic click, waveform, transcribe — using
 * Chromium's fake microphone fed from a WAV file (same getUserMedia → MediaRecorder
 * → /api/transcribe path as a human demo).
 *
 * Prereqs:
 *   1. Next.js dev server: npm run dev  (default http://localhost:3000)
 *   2. FastAPI backend on NEXT_PUBLIC_API_BASE_URL (default http://localhost:8000)
 *   3. ffmpeg (MP3 → WAV for Chromium). If Node can't see your User PATH, set
 *      FFMPEG_PATH=C:\\path\\to\\ffmpeg.exe
 *   4. One-time: npm install && npx playwright install chromium
 *
 * Usage (repo root):
 *   npm run demo:voice-e2e
 *   npm run demo:voice-e2e:attach   # attach to YOUR Chrome (see below — browser stays open)
 *   node scripts/e2e-mak-cik-rohani.mjs --record-seconds 10
 *   node scripts/e2e-mak-cik-rohani.mjs --cdp-url http://127.0.0.1:9222
 *   set HEADLESS=1 && node scripts/e2e-mak-cik-rohani.mjs
 *
 * Attach mode (--cdp / PLAYWRIGHT_CDP_URL):
 *   Start Chrome with CDP on 9222 + fake mic **before** attach (nothing on 9222 → ECONNREFUSED).
 *   Windows: `npm run demo:chrome-cdp` then `npm run demo:voice-e2e:attach`.
 *   Playwright disconnects at the end — your window stays open. See docs/DEMO_MAK_CIK_ROHANI.md.
 *
 * Env:
 *   BASE_URL              Frontend URL (default http://localhost:3000)
 *   PLAYWRIGHT_CDP_URL    e.g. http://127.0.0.1:9222 (attach instead of launch)
 *   CDP_URL               Alias for PLAYWRIGHT_CDP_URL
 *   AUDIO_MP3             Explicit path to source MP3
 *   PERSONA               elderly | migrant | rural (default rural)
 *   RECORD_MS             Ms to keep recording after mic start (default: auto from MP3 length + slack)
 *   RECORD_PADDING_MS     Extra ms after detected audio length (default 800)
 *   HEADLESS              1 = headless (ignored in attach mode)
 *   KEEP_OPEN_MS          If set, keep browser open this many ms before exit (launch mode)
 *   NO_BROWSER_CLOSE      1 = do not close Playwright-launched browser (launch mode only)
 *   FFMPEG_PATH           Full path to ffmpeg.exe if `ffmpeg` is not found (common when
 *                         npm is started from an IDE that doesn't load User PATH)
 */

import { chromium } from "playwright"
import { existsSync, mkdirSync, readdirSync, statSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { execSync, spawn, spawnSync } from "node:child_process"
import { platform } from "node:os"

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = resolve(__dirname, "..")
const CACHE_DIR = join(REPO_ROOT, "scripts", "demo-cache")
const WAV_CACHED = join(CACHE_DIR, "mak_cik_rohani_chromium.wav")

function findSourceMp3() {
  const envPath = process.env.AUDIO_MP3
  if (envPath && existsSync(envPath)) return resolve(envPath)

  const candidates = [
    join(REPO_ROOT, "public", "demo", "mak_cik_rohani.mp3"),
  ]
  for (const c of candidates) {
    if (existsSync(c)) return c
  }
  try {
    for (const name of readdirSync(REPO_ROOT)) {
      if (
        name.startsWith("ElevenLabs_") &&
        name.includes("Mak Cik Rohani") &&
        name.endsWith(".mp3")
      ) {
        return join(REPO_ROOT, name)
      }
    }
  } catch {
    /* */
  }
  return null
}

/**
 * Node (especially when launched from Cursor/VS Code) often does not inherit
 * Windows "User" PATH. Resolve ffmpeg explicitly.
 */
function resolveFfmpegExecutable() {
  const fromEnv = process.env.FFMPEG_PATH?.trim()
  if (fromEnv) {
    const p = resolve(fromEnv)
    if (existsSync(p)) return p
    console.warn(`FFMPEG_PATH set but file not found: ${p}`)
  }

  if (platform() === "win32") {
    try {
      // cmd.exe loads User + System PATH (same as your terminal after logon)
      const out = execSync("where ffmpeg", {
        encoding: "utf8",
        shell: "cmd.exe",
        windowsHide: true,
      }).trim()
      const first = out.split(/\r?\n/).filter(Boolean)[0]
      if (first && existsSync(first)) return first.trim()
    } catch {
      /* where failed */
    }

    for (const p of [
      "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
      "C:\\ffmpeg\\bin\\ffmpeg.exe",
      join(process.env.PROGRAMFILES || "C:\\Program Files", "ffmpeg", "bin", "ffmpeg.exe"),
    ]) {
      if (p && existsSync(p)) return p
    }
  }

  // Try plain name (works if process inherited PATH)
  const probe = spawnSync("ffmpeg", ["-version"], {
    encoding: "utf8",
    shell: platform() === "win32",
    windowsHide: true,
  })
  if (probe.status === 0) return "ffmpeg"

  if (platform() === "win32") {
    const probeExe = spawnSync("ffmpeg.exe", ["-version"], {
      encoding: "utf8",
      shell: true,
      windowsHide: true,
    })
    if (probeExe.status === 0) return "ffmpeg.exe"
  }

  return null
}

/** ffprobe lives next to ffmpeg (same WinGet / install layout). */
function resolveFfprobeExecutable(ffmpegExe) {
  if (!ffmpegExe) return null
  if (ffmpegExe === "ffmpeg") return "ffprobe"
  if (ffmpegExe === "ffmpeg.exe") return "ffprobe.exe"
  const replaced = ffmpegExe.replace(/ffmpeg\.exe$/i, "ffprobe.exe")
  if (replaced !== ffmpegExe) return replaced
  return ffmpegExe.replace(/ffmpeg$/i, "ffprobe")
}

/**
 * Duration of audio file in milliseconds (ceiled), or null if ffprobe fails.
 */
function getMediaDurationMs(mediaPath, ffmpegExe) {
  const ffprobe = resolveFfprobeExecutable(ffmpegExe)
  if (!ffprobe) return null
  const r = spawnSync(
    ffprobe,
    [
      "-v",
      "error",
      "-show_entries",
      "format=duration",
      "-of",
      "default=noprint_wrappers=1:nokey=1",
      mediaPath,
    ],
    { encoding: "utf8", shell: false, windowsHide: true }
  )
  if (r.status !== 0 || !r.stdout) return null
  const sec = parseFloat(String(r.stdout).trim(), 10)
  if (!Number.isFinite(sec) || sec <= 0) return null
  return Math.ceil(sec * 1000)
}

function ensureWavFromMp3(mp3Path) {
  mkdirSync(CACHE_DIR, { recursive: true })
  const needRebuild =
    !existsSync(WAV_CACHED) ||
    statSync(mp3Path).mtimeMs > statSync(WAV_CACHED).mtimeMs

  if (!needRebuild) {
    console.log(`Using cached WAV: ${WAV_CACHED}`)
    return WAV_CACHED
  }

  const ffmpegExe = resolveFfmpegExecutable()
  if (!ffmpegExe) {
    return null  // caller will handle this
  }

  console.log(`Using ffmpeg: ${ffmpegExe}`)

  const result = spawnSync(
    ffmpegExe,
    [
      "-y",
      "-i",
      mp3Path,
      "-ac",
      "1",
      "-ar",
      "44100",
      "-sample_fmt",
      "s16",
      "-c:a",
      "pcm_s16le",
      WAV_CACHED,
    ],
    {
      stdio: "inherit",
      shell: false,
      windowsHide: true,
    }
  )

  if (result.error) {
    console.error("ffmpeg spawn error:", result.error.message)
    process.exit(1)
  }
  if (result.status !== 0 && result.status !== null) {
    console.error(
      `\nffmpeg exited with code ${result.status}. If the MP3 path has special characters, try moving it to public/demo/mak_cik_rohani.mp3\n`
    )
    process.exit(1)
  }
  console.log(`Wrote WAV for Chromium fake mic: ${WAV_CACHED}`)
  return WAV_CACHED   // ensureWavFromMp3 guarantees non-null here
}

/**
 * Play the MP3 out loud through system speakers using ffplay (bundled with ffmpeg).
 * Runs non-blocking so the demo continues while audio plays.
 * Returns the spawned child process so the caller can kill it on stop.
 */
function playAudioLoud(mp3Path, ffmpegExe) {
  // ffplay is installed alongside ffmpeg in the same bin directory
  const ffplayExe = ffmpegExe === "ffmpeg" || ffmpegExe === "ffmpeg.exe"
    ? (platform() === "win32" ? "ffplay.exe" : "ffplay")
    : ffmpegExe.replace(/ffmpeg(\.exe)?$/i, (_, ext) => `ffplay${ext || ""}`)

  const ffplayExists = existsSync(ffplayExe)
    || ffplayExe === "ffplay"
    || ffplayExe === "ffplay.exe"

  if (!ffplayExists) {
    console.log(`(Speaker playback skipped — ffplay not found at ${ffplayExe})`)
    return null
  }

  console.log(`Playing audio: ${mp3Path}`)
  try {
    const child = spawn(
      ffplayExe,
      ["-nodisp", "-autoexit", "-loglevel", "quiet", mp3Path],
      { stdio: "ignore", detached: false, shell: false, windowsHide: true }
    )
    child.on("error", () => { /* ffplay not available — silently skip */ })
    return child
  } catch {
    return null
  }
}

function parseArgs() {
  const args = process.argv.slice(2)
  let recordSeconds = null
  let cdpUrlFromCli = null
  for (let i = 0; i < args.length; i++) {
    const a = args[i]
    if (a === "--record-seconds" && args[i + 1]) {
      recordSeconds = Number(args[i + 1])
      i++
    } else if (a === "--cdp") {
      cdpUrlFromCli = cdpUrlFromCli || "http://127.0.0.1:9222"
    } else if (a === "--cdp-url" && args[i + 1]) {
      cdpUrlFromCli = args[i + 1]
      i++
    } else if (a?.startsWith("--cdp-url=")) {
      cdpUrlFromCli = a.slice("--cdp-url=".length)
    }
  }
  const envCdp = (process.env.PLAYWRIGHT_CDP_URL || process.env.CDP_URL || "").trim()
  const cdpUrl = cdpUrlFromCli || envCdp || null
  return { recordSeconds, cdpUrl }
}

/**
 * Reuse an open /chat tab when attaching via CDP; otherwise use first tab or open /chat.
 */
async function attachPage(browser, chatUrl) {
  const contexts = browser.contexts()
  if (contexts.length === 0) {
    throw new Error(
      "No browser contexts from CDP. Is Chrome running with --remote-debugging-port?"
    )
  }

  const chatPath = new URL(chatUrl).pathname || "/chat"
  const matchesChat = (url) => {
    try {
      const u = new URL(url)
      return u.pathname === chatPath || u.pathname.startsWith(`${chatPath}/`)
    } catch {
      return url.includes("/chat")
    }
  }

  for (const ctx of contexts) {
    for (const p of ctx.pages()) {
      if (matchesChat(p.url())) {
        await p.bringToFront()
        return p
      }
    }
  }

  const ctx = contexts[0]
  const existing = ctx.pages()[0]
  if (existing) {
    await existing.bringToFront()
    if (!matchesChat(existing.url())) {
      await existing.goto(chatUrl, { waitUntil: "domcontentloaded", timeout: 60000 })
    }
    return existing
  }

  const page = await ctx.newPage()
  await page.goto(chatUrl, { waitUntil: "domcontentloaded", timeout: 60000 })
  return page
}

async function main() {
  const { recordSeconds, cdpUrl } = parseArgs()
  const baseUrl = (process.env.BASE_URL || "http://localhost:3000").replace(/\/$/, "")
  const chatUrl = `${baseUrl}/chat`
  const persona = (process.env.PERSONA || "rural").toLowerCase()
  const headless = process.env.HEADLESS === "1" || process.env.HEADLESS === "true"
  const keepOpenMs = process.env.KEEP_OPEN_MS
    ? Number(process.env.KEEP_OPEN_MS)
    : 0
  const attachMode = Boolean(cdpUrl)
  const skipCloseLaunch =
    !attachMode &&
    (process.env.NO_BROWSER_CLOSE === "1" || process.env.NO_BROWSER_CLOSE === "true")

  const mp3 = findSourceMp3()
  if (!mp3) {
    console.error(
      "No MP3 found. Place ElevenLabs_*Mak Cik Rohani*.mp3 in the repo root,\n" +
        "or public/demo/mak_cik_rohani.mp3, or set AUDIO_MP3=...\n"
    )
    process.exit(1)
  }

  const ffmpegExe = resolveFfmpegExecutable()
  if (!ffmpegExe) {
    console.error(
      "Cannot find ffmpeg. Set FFMPEG_PATH or add ffmpeg to System PATH.\n"
    )
    process.exit(1)
  }

  const paddingMs = Math.max(
    0,
    Number(process.env.RECORD_PADDING_MS || "800")
  )
  let recordMs
  if (recordSeconds != null && !Number.isNaN(recordSeconds)) {
    recordMs = Math.round(recordSeconds * 1000)
  } else if (
    process.env.RECORD_MS !== undefined &&
    process.env.RECORD_MS !== "" &&
    !Number.isNaN(Number(process.env.RECORD_MS))
  ) {
    recordMs = Number(process.env.RECORD_MS)
  } else {
    const detected = getMediaDurationMs(mp3, ffmpegExe)
    if (detected != null) {
      recordMs = detected + paddingMs
      console.log(
        `Record duration: ${recordMs}ms (source ~${detected}ms + RECORD_PADDING_MS=${paddingMs}). ` +
          "Override with RECORD_MS or --record-seconds."
      )
    } else {
      recordMs = 15000
      console.log(
        `Could not read MP3 duration (ffprobe); using RECORD_MS fallback ${recordMs}ms. ` +
          "Install ffprobe next to ffmpeg or set RECORD_MS."
      )
    }
  }

  const wavAbs = resolve(ensureWavFromMp3(mp3))
  // Chromium on Windows accepts forward slashes in this flag
  const wavForChromium = wavAbs.replace(/\\/g, "/")
  // When starting Chrome from cmd/PowerShell, paths with spaces must be quoted inside this flag
  const wavFlagForShell =
    /[\s]/.test(wavForChromium)
      ? `--use-file-for-fake-audio-capture="${wavForChromium}"`
      : `--use-file-for-fake-audio-capture=${wavForChromium}`

  console.log(`Source MP3: ${mp3}`)
  if (attachMode) {
    console.log(
      `Attach mode: CDP ${cdpUrl} (persona: ${persona}, record ~${recordMs}ms) — browser stays open after script exits.`
    )
    console.log(
      "Ensure this Chrome was started with fake mic flags + your WAV path:\n" +
        `  --use-fake-device-for-media-stream ${wavFlagForShell}`
    )
  } else {
    console.log(`Opening: ${chatUrl} (persona: ${persona}, record ~${recordMs}ms, headless=${headless})`)
  }

  let browser
  let page

  if (attachMode) {
    try {
      browser = await chromium.connectOverCDP(cdpUrl)
    } catch (err) {
      const msg = err?.message || String(err)
      const refused =
        msg.includes("ECONNREFUSED") ||
        err?.code === "ECONNREFUSED"
      if (refused) {
        console.error("\nCould not connect to Chrome DevTools (CDP). Nothing is listening on that port.\n")
        console.error(
          "Fix: run exactly `npm run demo:chrome-cdp` (no extra args), wait for “CDP is up”, then attach.\n" +
            "That script uses a separate Chrome profile so CDP works even if your normal Chrome is open.\n"
        )
        console.error("If you started Chrome manually, include --user-data-dir=... and --remote-debugging-port=9222.\n")
        console.error("  Or one line (chrome.exe path varies):")
        console.error(
          `    --remote-debugging-port=9222 --use-fake-device-for-media-stream ${wavFlagForShell}`
        )
        console.error(`Then open ${chatUrl} in that Chrome window and run this script again.\n`)
        console.error(`(Custom port: set PLAYWRIGHT_CDP_URL=http://127.0.0.1:PORT and start Chrome with --remote-debugging-port=PORT)\n`)
      } else {
        console.error(msg)
      }
      process.exit(1)
    }
    page = await attachPage(browser, chatUrl)
  } else {
    browser = await chromium.launch({
      headless,
      args: [
        "--use-fake-device-for-media-stream",
        `--use-file-for-fake-audio-capture=${wavForChromium}`,
        "--no-sandbox",
      ],
    })

    const context = await browser.newContext({
      viewport: { width: 1400, height: 900 },
      ignoreHTTPSErrors: true,
      permissions: ["microphone"],
    })

    page = await context.newPage()
    await page.goto(chatUrl, { waitUntil: "domcontentloaded", timeout: 60000 })
  }

  page.on("console", (msg) => {
    if (msg.type() === "error") console.log("[browser]", msg.text())
  })

  // Persona (sidebar)
  const personaLabel =
    persona === "elderly"
      ? "Elderly"
      : persona === "migrant"
        ? "Migrant Worker"
        : "Rural Community"
  await page.getByRole("button", { name: personaLabel }).click({ timeout: 15000 })

  // Mic = same control as a user click (pointer handler on real app)
  const mic = page.getByRole("button", { name: "Start voice input" })
  await mic.click({ timeout: 15000 })

  await page.getByRole("button", { name: "Stop recording" }).waitFor({
    state: "visible",
    timeout: 10000,
  })
  console.log("Recording UI: Stop button visible")

  await page.getByTestId("voice-waveform").waitFor({
    state: "visible",
    timeout: 5000,
  })
  console.log("Waveform visible (reactive bars)")

  // Play the MP3 out loud so the audience can hear what Mak Cik Rohani says
  const audioPlayer = playAudioLoud(mp3, ffmpegExe)

  await new Promise((r) => setTimeout(r, recordMs))

  // Stop speaker playback and browser recording together
  if (audioPlayer) {
    try { audioPlayer.kill() } catch { /* already finished */ }
  }
  await page.getByRole("button", { name: "Stop recording" }).click()
  console.log("Stopped recording — waiting for transcription…")

  try {
    await page.getByText("Transcribing…", { exact: false }).waitFor({
      state: "visible",
      timeout: 8000,
    })
    console.log("Transcribing… shown")
  } catch {
    console.log("(Transcribing… not seen — may be too fast)")
  }

  const input = page.getByRole("textbox", { name: "Chat input" })
  await input.waitFor({ state: "visible", timeout: 5000 })
  await page.waitForFunction(
    () => {
      const el = document.querySelector('input[aria-label="Chat input"]')
      return el && el.value && el.value.trim().length > 1
    },
    null,
    { timeout: 120000 }
  )

  const transcript = await input.inputValue()
  console.log("\n── Transcript (input field) ──")
  console.log(transcript)
  console.log("─────────────────────────────\n")

  if (keepOpenMs > 0 && !attachMode) {
    console.log(`KEEP_OPEN_MS=${keepOpenMs} — browser stays open for inspection.`)
    await new Promise((r) => setTimeout(r, keepOpenMs))
  }

  if (attachMode) {
    // CDP: closes Playwright connection only; leaves your Chrome running
    await browser.close()
    console.log("Done — disconnected from browser (your window stays open for demo).")
  } else if (skipCloseLaunch) {
    console.log("Done — NO_BROWSER_CLOSE: leaving Playwright-launched browser open.")
  } else {
    await browser.close()
    console.log("Done.")
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
