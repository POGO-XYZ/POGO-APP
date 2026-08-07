# POGO Studios — Archive & Tools

The application layer of the [POGO Studios Archive](https://github.com/POGO-XYZ/POGO-ARCHIVE): a public interface for viewing, verifying, and exploring every physical artwork the studio has documented.

**Live at [pogo-xyz.github.io/POGO-APP](https://pogo-xyz.github.io/POGO-APP/)**

Everything here runs entirely in the browser. There is no server, no account, no tracking, and nothing is uploaded. The app only reads public files — it cannot alter the archive.

---

## What's here

### Archive

Every documented work, browsable as a grid or searchable by ID. Each record shows its full details, availability, provenance across the physical, digital, and cryptographic layers, and its recorded fingerprint.

Any work can be **verified in the browser**: the app fetches the canonical image, computes its SHA-256 hash locally, and compares it against the fingerprint recorded at the time of archiving. Nothing is taken on trust — the check runs on the visitor's own machine.

Every work has a permanent address:

```
archive.html?id=POGO-2026-PO-FZ
```

### Tool 001 — Text Renderer

Renders any archived work as ASCII or Unicode Braille, with adjustable detail, dithering, colour, and export to `.txt` or `.png`. Only archived works can be rendered; there is no upload.

### Tool 002 — Live Sequence

A continuously running sequence through the archive, moving between works by tonal similarity rather than at random. Adjustable pace, character set, and background, with adaptive quality that matches the device it's running on. Records to video for use elsewhere.

---

## Installing

The app can be installed to a phone or desktop and used offline.

- **Android / Chrome / Edge** — an install option appears on the home page, or use the browser's install action.
- **iOS / Safari** — tap Share, then *Add to Home Screen*.
- **Desktop** — an install icon appears in the address bar.

Once installed it launches without browser chrome and keeps working without a connection, using the last data it retrieved.

---

## How the data works

The app reads from three sources, all public:

| Source | Provides |
|---|---|
| [POGO-ARCHIVE](https://github.com/POGO-XYZ/POGO-ARCHIVE) | Records, indexes, listings, proofs |
| [POGO-ARCHIVE-MEDIA](https://github.com/POGO-XYZ/POGO-ARCHIVE-MEDIA) | Canonical artwork images |
| `manifest.json` (here) | A flattened index of every work, generated from the two above |

The manifest exists so the app makes one request instead of dozens. It is generated, not hand-written, and should be rebuilt whenever works are archived:

```bash
python3 build-manifest.py
```

This reads the sibling archive repositories, writes `manifest.json`, generates thumbnails into `thumbs/`, and reports any records missing media or media missing records. It requires Pillow (`pip3 install pillow`).

Commit the regenerated manifest and thumbnails alongside the records they describe.

---

## Structure

```
index.html                        landing page
archive.html                      the archive browser
text-renderer.html                Tool 001
art-to-text-live-sequence.html    Tool 002
build-manifest.py                 manifest and thumbnail generator
manifest.json                     generated — do not edit by hand
thumbs/                           generated grid thumbnails
fonts.css  fonts/                 self-hosted typography
icons/  app.webmanifest  sw.js    installable app support
```

Deliberately dependency-light: no build step, no framework, no package manager. Every page is a single file that will still run in a browser years from now.

---

## Related

- [POGO-ARCHIVE](https://github.com/POGO-XYZ/POGO-ARCHIVE) — the primary record
- [POGO-ARCHIVE-MEDIA](https://github.com/POGO-XYZ/POGO-ARCHIVE-MEDIA) — canonical media
- [All Creation Testifies](https://www.pogostudios.xyz/writings/all-creation-testifies) — the philosophy behind the system
- [pogostudios.xyz](https://www.pogostudios.xyz) — studio and collection access

---

## License

© 2025–2026 POGO Studios. [POGO Studios Archive — System Documentation and Philosophical Framework](https://github.com/POGO-XYZ/POGO-ARCHIVE) by [POGO Studios](https://www.pogostudios.xyz) is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt this material for any purpose provided appropriate credit is given to POGO Studios as the originating source.

[![CC BY 4.0](https://mirrors.creativecommons.org/presskit/buttons/88x31/svg/by.svg)](https://creativecommons.org/licenses/by/4.0/)
