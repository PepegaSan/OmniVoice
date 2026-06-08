#!/usr/bin/env python3
# Modified by PepegaSan (2026) — see CHANGELOG.md and NOTICE.
# Based on OmniVoice by k2-fsa/Xiaomi Corp. (Apache-2.0).
"""Einfache deutsche Web-UI für OmniVoice (Voice Cloning)."""

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import gradio as gr
import numpy as np
import soundfile as sf
import torch
from pydub import AudioSegment

from omnivoice import OmniVoice, OmniVoiceGenerationConfig
from omnivoice.models.omnivoice import VoiceClonePrompt

SAVED_VOICES_DIR = Path(__file__).resolve().parent / "saved_voices"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

NONVERBAL_TAGS = [
    ("", "(keins)"),
    ("[laughter]", "Lachen"),
    ("[sigh]", "Seufzen"),
    ("[confirmation-en]", "Bestätigung (en)"),
    ("[question-en]", "Frage (en)"),
    ("[question-ah]", "Frage (ah)"),
    ("[question-oh]", "Frage (oh)"),
    ("[question-ei]", "Frage (ei)"),
    ("[question-yi]", "Frage (yi)"),
    ("[surprise-ah]", "Überraschung (ah)"),
    ("[surprise-oh]", "Überraschung (oh)"),
    ("[surprise-wa]", "Überraschung (wa)"),
    ("[surprise-yo]", "Überraschung (yo)"),
    ("[dissatisfaction-hnn]", "Unzufriedenheit (hmm)"),
]

TAG_CHOICES = [f"{tag} – {label}" if tag else label for tag, label in NONVERBAL_TAGS]
TAG_LOOKUP = {f"{tag} – {label}" if tag else label: tag for tag, label in NONVERBAL_TAGS}


def load_model(model_id: str, device: str, with_asr: bool) -> OmniVoice:
    return OmniVoice.from_pretrained(
        model_id,
        device_map=device,
        dtype=torch.float16,
        load_asr=with_asr,
    )


def sanitize_voice_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Bitte einen Namen eingeben.")
    if not re.fullmatch(r"[\w\-. ]+", name, flags=re.UNICODE):
        raise ValueError("Nur Buchstaben, Zahlen, Leerzeichen, - und _ erlaubt.")
    return name


def list_saved_voices() -> list[str]:
    if not SAVED_VOICES_DIR.exists():
        return []
    return sorted(
        d.name
        for d in SAVED_VOICES_DIR.iterdir()
        if d.is_dir() and (d / "meta.json").exists() and (d / "ref.wav").exists()
    )


def selected_tag_value(tag_choice: str) -> str:
    return TAG_LOOKUP.get(tag_choice, "")


def cleanup_output_dir(keep: str | Path | None = None) -> None:
    """Löscht alte Ausgabedateien. Optional eine Datei behalten."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    keep_path = Path(keep).resolve() if keep else None
    for path in OUTPUT_DIR.iterdir():
        if not path.is_file():
            continue
        if keep_path is not None and path.resolve() == keep_path:
            continue
        path.unlink(missing_ok=True)


def build_download_name(saved_voice: str, voice_name: str) -> str:
    if saved_voice and saved_voice != "(keine)":
        base = saved_voice
    elif voice_name and voice_name.strip():
        base = voice_name.strip()
    else:
        base = "omnivoice"
    base = re.sub(r"[^\w\-.]+", "_", base.strip(), flags=re.UNICODE)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{ts}"


def write_output_audio(waveform_int16: np.ndarray, sr: int, basename: str, fmt: str) -> tuple[str, str]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = OUTPUT_DIR / f"{basename}.wav"
    float_audio = waveform_int16.astype(np.float32) / 32767.0
    sf.write(wav_path, float_audio, sr)

    if fmt.lower() == "wav":
        return str(wav_path), f"Gespeichert als {wav_path.name}"

    mp3_path = OUTPUT_DIR / f"{basename}.mp3"
    try:
        segment = AudioSegment.from_wav(str(wav_path))
        segment.export(str(mp3_path), format="mp3", bitrate="192k")
        wav_path.unlink(missing_ok=True)
        return str(mp3_path), f"Gespeichert als {mp3_path.name}"
    except Exception as exc:
        return (
            str(wav_path),
            f"MP3 fehlgeschlagen ({exc}). Als WAV gespeichert: {wav_path.name}. "
            "Für MP3 ffmpeg installieren und im PATH verfügbar machen.",
        )


def build_ui(model: OmniVoice) -> gr.Blocks:
    sr = model.sampling_rate
    prompt_cache: dict[str, VoiceClonePrompt] = {}

    def refresh_voice_dropdown():
        voices = list_saved_voices()
        return gr.Dropdown(choices=["(keine)"] + voices, value="(keine)")

    def load_prompt_from_disk(name: str) -> VoiceClonePrompt | None:
        if name in prompt_cache:
            return prompt_cache[name]

        pt_path = SAVED_VOICES_DIR / name / "prompt.pt"
        if pt_path.exists():
            data = torch.load(pt_path, map_location=model.device, weights_only=True)
            prompt = VoiceClonePrompt(
                ref_audio_tokens=data["ref_audio_tokens"].to(model.device),
                ref_text=data["ref_text"],
                ref_rms=data["ref_rms"],
            )
            prompt_cache[name] = prompt
            return prompt

        ref_path = SAVED_VOICES_DIR / name / "ref.wav"
        meta_path = SAVED_VOICES_DIR / name / "meta.json"
        if ref_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ref_text = meta.get("ref_text") or None
            prompt = model.create_voice_clone_prompt(
                ref_audio=str(ref_path),
                ref_text=ref_text,
            )
            prompt_cache[name] = prompt
            return prompt

        return None

    def save_voice(name, ref_audio, ref_text):
        try:
            voice_name = sanitize_voice_name(name)
        except ValueError as exc:
            return str(exc), gr.Dropdown()

        if not ref_audio:
            return "Bitte zuerst Referenz-Audio hochladen.", gr.Dropdown()

        voice_dir = SAVED_VOICES_DIR / voice_name
        voice_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ref_audio, voice_dir / "ref.wav")
        meta = {"ref_text": (ref_text or "").strip()}
        (voice_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        prompt = model.create_voice_clone_prompt(
            ref_audio=str(voice_dir / "ref.wav"),
            ref_text=meta["ref_text"] or None,
        )
        prompt_cache[voice_name] = prompt
        torch.save(
            {
                "ref_audio_tokens": prompt.ref_audio_tokens.cpu(),
                "ref_text": prompt.ref_text,
                "ref_rms": prompt.ref_rms,
            },
            voice_dir / "prompt.pt",
        )

        voices = ["(keine)"] + list_saved_voices()
        return f"Stimme '{voice_name}' gespeichert.", gr.Dropdown(choices=voices, value=voice_name)

    def load_saved_voice(name):
        if not name or name == "(keine)":
            return None, "", "Keine gespeicherte Stimme ausgewählt."

        voice_dir = SAVED_VOICES_DIR / name
        ref_path = voice_dir / "ref.wav"
        meta_path = voice_dir / "meta.json"
        if not ref_path.exists() or not meta_path.exists():
            return None, "", f"Stimme '{name}' nicht gefunden."

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        load_prompt_from_disk(name)
        return str(ref_path), meta.get("ref_text", ""), f"Stimme '{name}' geladen."

    def delete_voice(name):
        if not name or name == "(keine)":
            return "Keine Stimme zum Löschen ausgewählt.", gr.Dropdown()

        voice_dir = SAVED_VOICES_DIR / name
        if voice_dir.exists():
            shutil.rmtree(voice_dir)
        prompt_cache.pop(name, None)

        voices = ["(keine)"] + list_saved_voices()
        return f"Stimme '{name}' gelöscht.", gr.Dropdown(choices=voices, value="(keine)")

    def show_selected_tag(tag_choice):
        tag = selected_tag_value(tag_choice)
        if tag:
            return tag, f"Tag bereit: {tag} — kopieren und mit Strg+V einfügen."
        return "", "Kein Tag ausgewählt."

    def copy_tag_notice(tag):
        if tag:
            return f"'{tag}' in Zwischenablage — mit Strg+V im Text einfügen."
        return "Kein Tag ausgewählt."

    def generate(text, ref_audio, ref_text, saved_voice, voice_name, output_format, language, steps, speed):
        if not text or not text.strip():
            return None, "Bitte Text eingeben."

        final_text = text.strip()
        lang = None if not language or language == "Auto" else language
        config = OmniVoiceGenerationConfig(num_step=int(steps), denoise=True)

        kwargs = {
            "text": final_text,
            "language": lang,
            "generation_config": config,
        }
        if speed and float(speed) != 1.0:
            kwargs["speed"] = float(speed)

        try:
            if saved_voice and saved_voice != "(keine)":
                prompt = load_prompt_from_disk(saved_voice)
                if prompt is None:
                    return None, f"Gespeicherte Stimme '{saved_voice}' konnte nicht geladen werden."
                kwargs["voice_clone_prompt"] = prompt
            elif ref_audio:
                kwargs["voice_clone_prompt"] = model.create_voice_clone_prompt(
                    ref_audio=ref_audio,
                    ref_text=ref_text.strip() or None,
                )

            audio = model.generate(**kwargs)
        except Exception as exc:
            return None, f"Fehler: {type(exc).__name__}: {exc}"

        waveform = (audio[0] * 32767).astype(np.int16)
        cleanup_output_dir()
        basename = build_download_name(saved_voice, voice_name)
        filepath, msg = write_output_audio(waveform, sr, basename, output_format)
        return filepath, f"{msg} — alte Dateien im outputs-Ordner wurden entfernt."

    with gr.Blocks(title="OmniVoice – Einfache UI") as demo:
        gr.Markdown(
            """
# OmniVoice – Einfache Web-UI

Text eingeben, optional Referenz-Audio hochladen oder **gespeicherte Stimme** wählen, dann **Generieren**.
"""
        )

        with gr.Row():
            with gr.Column():
                text = gr.Textbox(
                    label="Text",
                    lines=4,
                    placeholder="Hier den zu sprechenden Text eingeben...",
                )

                nonverbal_tag = gr.Dropdown(
                    label="Non-verbaler Tag",
                    choices=TAG_CHOICES,
                    value="(keins)",
                )
                tag_preview = gr.Textbox(
                    label="Tag zum Kopieren",
                    interactive=False,
                )
                copy_tag_btn = gr.Button("In Zwischenablage kopieren")
                gr.Markdown(
                    "<span style='font-size:0.9em;color:#666;'>"
                    "Tag kopieren und im Textfeld an beliebiger Stelle mit Strg+V einfügen."
                    "</span>"
                )

                gr.Markdown("### Stimme")
                saved_voice = gr.Dropdown(
                    label="Gespeicherte Stimme",
                    choices=["(keine)"] + list_saved_voices(),
                    value="(keine)",
                )
                with gr.Row():
                    load_voice_btn = gr.Button("Stimme laden")
                    refresh_voices_btn = gr.Button("Liste aktualisieren")

                ref_audio = gr.Audio(label="Referenz-Audio (optional)", type="filepath")
                ref_text = gr.Textbox(
                    label="Referenz-Text (optional)",
                    placeholder="Transkript des Referenz-Audios.",
                )

                with gr.Row():
                    voice_name = gr.Textbox(
                        label="Name für Speichern",
                        placeholder="z.B. meine-stimme",
                        scale=2,
                    )
                    save_voice_btn = gr.Button("Stimme speichern", variant="secondary")
                delete_voice_btn = gr.Button("Ausgewählte Stimme löschen", variant="stop")

                language = gr.Dropdown(
                    label="Sprache",
                    choices=["Auto", "German", "English", "French", "Spanish", "Italian"],
                    value="Auto",
                )
                steps = gr.Slider(8, 64, value=32, step=1, label="Inference Steps")
                speed = gr.Slider(0.5, 1.5, value=1.0, step=0.05, label="Geschwindigkeit")
                output_format = gr.Radio(
                    label="Download-Format",
                    choices=["MP3", "WAV"],
                    value="MP3",
                )
                btn = gr.Button("Generieren", variant="primary")

            with gr.Column():
                output = gr.Audio(label="Ergebnis", type="filepath")
                btn_bottom = gr.Button("Generieren", variant="primary")
                status = gr.Textbox(label="Status")
                gr.Markdown(
                    "<span style='font-size:0.9em;color:#666;'>"
                    "Download mit Stimmenname. Alte Dateien werden beim nächsten Generieren "
                    "und beim Neustart der UI automatisch gelöscht."
                    "</span>"
                )

        nonverbal_tag.change(
            show_selected_tag,
            inputs=[nonverbal_tag],
            outputs=[tag_preview, status],
        )
        copy_tag_btn.click(
            copy_tag_notice,
            inputs=[tag_preview],
            outputs=[status],
            js="(tag) => { if (tag) navigator.clipboard.writeText(tag); }",
        )
        save_voice_btn.click(
            save_voice,
            inputs=[voice_name, ref_audio, ref_text],
            outputs=[status, saved_voice],
        )
        load_voice_btn.click(
            load_saved_voice,
            inputs=[saved_voice],
            outputs=[ref_audio, ref_text, status],
        )
        refresh_voices_btn.click(refresh_voice_dropdown, outputs=[saved_voice])
        delete_voice_btn.click(delete_voice, inputs=[saved_voice], outputs=[status, saved_voice])
        generate_inputs = [
            text,
            ref_audio,
            ref_text,
            saved_voice,
            voice_name,
            output_format,
            language,
            steps,
            speed,
        ]
        generate_outputs = [output, status]
        btn.click(generate, inputs=generate_inputs, outputs=generate_outputs)
        btn_bottom.click(generate, inputs=generate_inputs, outputs=generate_outputs)

    return demo


def main():
    parser = argparse.ArgumentParser(description="Einfache OmniVoice Web-UI")
    parser.add_argument("--model", default="k2-fsa/OmniVoice")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument(
        "--with-asr",
        action="store_true",
        help="Whisper laden (langsamer Start, ~1.5 GB extra). Nur nötig für Auto-Transkription.",
    )
    args = parser.parse_args()

    SAVED_VOICES_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_output_dir()

    print(f"Lade Modell: {args.model} auf {args.device} ...")
    if not args.with_asr:
        print(
            "ASR deaktiviert (schnellerer Start). "
            "Referenz-Text manuell eingeben oder --with-asr nutzen."
        )
    model = load_model(args.model, args.device, args.with_asr)
    print("Modell geladen. Starte Web-UI ...")

    ui = build_ui(model)
    ui.queue().launch(server_name=args.ip, server_port=args.port)


if __name__ == "__main__":
    main()
