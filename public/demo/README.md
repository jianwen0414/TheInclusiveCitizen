# Demo audio (optional)

## Mak Cik Rohani (Kelantanese / rural persona)

`mak_cik_rohani.mp3` can live here for:

- **Playwright E2E** (`npm run demo:voice-e2e`) — the script also accepts `ElevenLabs_*Mak Cik Rohani*.mp3` in the repo root.

```powershell
.\scripts\copy_rohani_demo_audio.ps1
```

See **`docs/DEMO_MAK_CIK_ROHANI.md`**.

## Budi (migrant worker — Indonesian / Javanese)

`budi.mp3` for **`npm run demo:voice-e2e:budi`** (or `ElevenLabs_*Budi*.mp3` in repo root).

```powershell
.\scripts\copy_budi_demo_audio.ps1
```

See **`docs/DEMO_BUDI.md`**.

---

### Chrome CDP + fake mic

- Rohani: `npm run demo:chrome-cdp` → `npm run demo:voice-e2e:attach`
- Budi: `npm run demo:chrome-cdp:budi` → `npm run demo:voice-e2e:budi:attach`