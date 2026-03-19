#!/usr/bin/env python3
"""
Headless: POST Mak Cik Rohani's MP3 to /api/transcribe (and optionally /api/query).
Same multipart as the browser; no UI. For full mic + waveform + /chat, use:
  npm run demo:voice-e2e
  (see docs/DEMO_MAK_CIK_ROHANI.md)

Usage (from repo root, backend running on :8000):
  python scripts/demo_mak_cik_rohani.py
  python scripts/demo_mak_cik_rohani.py --full-query --persona rural

Prerequisites:
  pip install requests  (or use backend venv: ..\\backend\\.venv\\Scripts\\python)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def find_default_mp3(repo_root: Path) -> Path | None:
    for p in repo_root.glob("ElevenLabs_*Mak Cik Rohani*.mp3"):
        return p
    alt = repo_root / "public" / "demo" / "mak_cik_rohani.mp3"
    if alt.is_file():
        return alt
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Mak Cik Rohani voice → transcribe (+ optional query)")
    parser.add_argument(
        "--audio",
        type=Path,
        help="Path to MP3 (default: ElevenLabs_*Mak Cik Rohani*.mp3 in repo root or public/demo/mak_cik_rohani.mp3)",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="FastAPI base URL")
    parser.add_argument("--full-query", action="store_true", help="After STT, POST /api/query with transcript")
    parser.add_argument(
        "--persona",
        default="rural",
        choices=("elderly", "migrant", "rural"),
        help="Persona for /api/query (PRD: Mak Cik Rohani → rural community)",
    )
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("Install requests: pip install requests", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    audio_path = args.audio
    if audio_path is None:
        found = find_default_mp3(repo_root)
        if not found:
            print(
                "No MP3 found. Place ElevenLabs_*Mak Cik Rohani*.mp3 in repo root or run scripts/copy_rohani_demo_audio.ps1",
                file=sys.stderr,
            )
            return 1
        audio_path = found

    if not audio_path.is_file():
        print(f"Audio file not found: {audio_path}", file=sys.stderr)
        return 1

    base = args.base_url.rstrip("/")
    print(f"Audio: {audio_path} ({audio_path.stat().st_size} bytes)")
    print(f"POST {base}/api/transcribe …")

    t0 = time.perf_counter()
    with audio_path.open("rb") as f:
        files = {"file": (audio_path.name, f, "audio/mpeg")}
        r = requests.post(f"{base}/api/transcribe", files=files, timeout=120)
    transcribe_ms = (time.perf_counter() - t0) * 1000

    if not r.ok:
        print(f"Transcribe failed HTTP {r.status_code}: {r.text}", file=sys.stderr)
        return 1

    data = r.json()
    text = data.get("text", "")
    lang = data.get("detected_language", "")
    print(f"[transcribe] {transcribe_ms:.0f} ms")
    print(f"  detected_language: {lang}")
    print(f"  text:\n{text}\n")

    if args.full_query:
        print(f"POST {base}/api/query persona={args.persona} …")
        t1 = time.perf_counter()
        qr = requests.post(
            f"{base}/api/query",
            headers={"Content-Type": "application/json"},
            json={
                "query": text,
                "persona": args.persona,
                "language": lang or None,
            },
            timeout=300,
        )
        query_ms = (time.perf_counter() - t1) * 1000
        if not qr.ok:
            print(f"Query failed HTTP {qr.status_code}: {qr.text}", file=sys.stderr)
            return 1
        body = qr.json()
        print(f"[query] {query_ms:.0f} ms")
        print(f"  answer (first 500 chars):\n{body.get('answer', '')[:500]}…\n")
        print(json.dumps({k: body[k] for k in ("detected_language", "confidence", "semantic_score") if k in body}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
