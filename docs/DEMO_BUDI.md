# Budi (migrant worker) - voice demo pack

Same mechanics as **Mak Cik Rohani** (`docs/DEMO_MAK_CIK_ROHANI.md`): ElevenLabs MP3 -> optional `public/demo/budi.mp3` -> Playwright fake mic on **`/chat`** with persona **Migrant Worker**.

## 1) ElevenLabs Voice Design prompt (Budi)

Use **Voice Design** in the ElevenLabs app and follow their [prompting guide](https://elevenlabs.io/docs/eleven-creative/voices/voice-design#prompting-guide) (recommended structure: native language, demographics, quality, persona, emotion, timbre/pacing).

**Copy-paste prompt:**

```text
Native Indonesian with Central Javanese (Ngoko) colouring - code-mixes polite Javanese forms with standard Indonesian job/admin vocabulary. Male, 28-35. Very good quality. Persona: migrant factory worker in Malaysia. Emotion: earnest, respectful, a little tired but hopeful.

Warm, slightly nasal mid-pitched male timbre; conversational pacing with short natural pauses; clear consonants on bureaucratic words (permit, passport, majikan). Forward studio proximity, clean signal, no reverb, no phone FX. Speaks like he is asking a counter officer for help - humble, not theatrical.
```

**Text to preview:** paste the Budi sentence from section 2 into the "Text to preview" field so the model locks onto the right accent and code-mix. Per ElevenLabs docs, longer preview text stabilises tone and accent - do not use a shorter placeholder.

## 2) Sentence for Budi to say (Javanese + BI)

Use this for the ElevenLabs export **and** as the expected STT input.
It is **intentionally mixed**: Ngoko Javanese + standard Indonesian administrative words a migrant worker in Malaysia would use.
Topic is **work permit renewal** (consistent with the work-permit docs in the knowledge base).

```text
Kulo njaluk pirsa, pak. Kulo durung ngerti carane ngurus perpanjangan permit kerja. Dokumene durung lengkap, kok wes meh tutup tanggale. Tolong panjenengan jelasna langkahe, yo.
```

**Gloss (for your script):** "I want to ask, sir. I still don't understand how to renew my work permit. The documents aren't complete yet, but the deadline is almost closed. Please explain the steps, yeah."

**Key Javanese markers that trigger `jv` detection:** `kulo`, `njaluk`, `durung`, `ngerti`, `panjenengan`, `wes`, `kok` - the detector fires on >= 2 hits.

**Optional pure Bahasa Indonesia line** (stays `id`, no Ngoko):
`Saya mau tanya, pak. Saya belum mengerti cara memperpanjang permit kerja saya. Dokumen saya belum lengkap, tapi deadline perpanjangannya sudah dekat. Tolong jelaskan langkah-langkahnya.`

## 3) Scripts (parity with Mak Cik Rohani)

| Purpose | Command / file |
|--------|------------------|
| Copy ElevenLabs export into `public/demo/budi.mp3` | `.\scripts\copy_budi_demo_audio.ps1` |
| Headless: `POST /api/transcribe` (+ optional `/api/query`) | `python scripts/demo_budi.py` |
| Full UI E2E (Playwright fake mic) | `npm run demo:voice-e2e:budi` |
| Chrome CDP + fake mic for **Budi** WAV | `npm run demo:chrome-cdp:budi` then `npm run demo:voice-e2e:budi:attach` |

Environment (same as Rohani E2E): `AUDIO_MP3`, `BASE_URL`, `PLAYWRIGHT_CDP_URL`, `RECORD_MS`, etc. Default **persona** for `--demo budi` is **migrant** (override with `--persona` or `PERSONA`).

---

## Pipeline note: Bahasa Indonesia vs Javanese vs Malay

- **Malay (`ms`)** and **Indonesian (`id`)** are close; the detector previously collapsed both to Malaysian Malay for typed queries. Now split: **`ms` -> Malay dialects / BM**, **`id` -> Bahasa Indonesia**, **Javanese-heavy text -> `jv`** via lexical cues.
- **Javanese is a separate language**, not a Malaysian dialect. The backend routes `jv` through direct LLM generation (same tier as `id`) and uses Indonesian Google TTS as the closest Cloud TTS fallback (no Javanese locale in Cloud TTS).
- **Voice path:** STT may label Javanese speech as `id`; the server refines to `jv` when the transcript has enough Javanese markers.
- **Lingua-py** frequently labels Javanese text as `ms` (not just `id`) because both are Latin-script Austronesian languages. The fix: `detect_javanese_from_text()` now runs **before** the Malay/Indonesian branch decisions, not after.

For a **pure Bahasa Indonesia** Budi demo (no Ngoko), use the plain BI copy above - detection will stay `id`.
