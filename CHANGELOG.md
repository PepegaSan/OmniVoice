# Changelog — PepegaSan Fork

This file documents modifications made to the upstream
[k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) project, as required by
the [Apache License 2.0](LICENSE) (Section 4(a): *"You must cause any modified
files to carry prominent notices stating that You changed the files"*).

**Upstream:** k2-fsa/OmniVoice (Apache-2.0)  
**Fork maintainer:** [PepegaSan](https://github.com/PepegaSan)  
**Fork repository:** https://github.com/PepegaSan/OmniVoice

---

## [Unreleased] — 2026-06-08

### Added

- **`simple_webui.py`** — German Gradio web UI with:
  - Voice profile save/load/delete (`saved_voices/`)
  - Non-verbal tag dropdown with clipboard copy
  - MP3/WAV export with voice name in filename (`outputs/`)
  - Second generate button below audio output
  - Automatic cleanup of old files in `outputs/`
- **`install.bat`** — Windows installation (venv, PyTorch CUDA, editable install)
- **`start_simple_webui.bat`** — Start simple web UI (auto-kills port conflict)
- **`start_webui.bat`** — Start official `omnivoice-demo`
- **`kill_port.bat`** — Helper to free the Gradio port before startup
- **`install.ps1`**, **`start_simple_webui.ps1`**, **`start_webui.ps1`** — PowerShell alternatives
- **`check_install.py`** — Quick CUDA / omnivoice install verification script
- **`NOTICE`** — Attribution for upstream and this derivative work
- **`CHANGELOG.md`** — This file

### Changed

- **`README.md`** — Fork notice, quick-start for Windows `.bat` launchers, link to changelog
- **`.gitignore`** — Ignore `outputs/`, `saved_voices/`, local runtime data

### Unchanged from upstream

- Core `omnivoice/` package, model weights, training scripts, official CLI (`omnivoice-demo`), and `LICENSE` remain from the upstream project unless listed above.

---

## Attribution

Original work © contributors to [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice)
(Xiaomi Corp. / Next-gen Kaldi team). Licensed under Apache License 2.0.

Modifications in this fork © PepegaSan. Distributed under the same Apache License 2.0.
See [LICENSE](LICENSE) for full terms.
