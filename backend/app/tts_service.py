from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
from pathlib import Path

DEFAULT_VOICE_NAME = "Microsoft Huihui Desktop"
DEFAULT_EDGE_VOICE_NAME = "zh-CN-XiaoxiaoNeural"
DEFAULT_RATE = -2
DEFAULT_VOLUME = 96
DEFAULT_TTS_ENGINE = "auto"


def render_speech_audio(
    speech_script_path: Path,
    output_path: Path,
    voice_name: str = DEFAULT_VOICE_NAME,
    rate: int = DEFAULT_RATE,
    volume: int = DEFAULT_VOLUME,
) -> Path | None:
    if not speech_script_path.exists():
        return None

    speech_items = json.loads(speech_script_path.read_text(encoding="utf-8-sig"))
    if not speech_items:
        return None

    engine = env_text("TTS_ENGINE", DEFAULT_TTS_ENGINE).lower()
    edge_voice = env_text("TTS_VOICE", DEFAULT_EDGE_VOICE_NAME)

    if engine in {"auto", "edge", "neural"} and edge_tts_available():
        try:
            return render_edge_audio(
                speech_items,
                output_path,
                voice_name=edge_voice,
                rate=env_text("TTS_EDGE_RATE", "-8%"),
                volume=env_text("TTS_EDGE_VOLUME", "+0%"),
            )
        except Exception as error:
            if engine in {"edge", "neural"}:
                raise RuntimeError(f"Edge TTS render failed: {error}") from error
            print("Online neural TTS failed, falling back to Windows SAPI.")
            print(f"Error: {error}")
            print("")

    return render_windows_sapi_audio(speech_script_path, output_path, voice_name, rate, volume)


def render_edge_audio(
    speech_items: list[dict],
    output_path: Path,
    voice_name: str,
    rate: str,
    volume: str,
) -> Path | None:
    import edge_tts  # type: ignore

    text = build_edge_text(speech_items)
    if not text:
        return None

    audio_path = output_path.with_suffix(".mp3") if output_path.suffix.lower() != ".mp3" else output_path
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    if audio_path.exists():
        audio_path.unlink()

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_name,
        rate=rate,
        volume=volume,
        pitch="+0Hz",
    )
    asyncio.run(communicate.save(str(audio_path)))
    if not audio_path.exists():
        raise RuntimeError("edge_tts did not create audio output")
    return audio_path


def render_windows_sapi_audio(
    speech_script_path: Path,
    output_path: Path,
    voice_name: str,
    rate: int,
    volume: int,
) -> Path | None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        build_powershell_script(speech_script_path, output_path, voice_name, rate, volume),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError((result.stderr or result.stdout or "tts render failed")[-2000:])
    return output_path


def build_powershell_script(speech_script_path: Path, output_path: Path, voice_name: str, rate: int, volume: int) -> str:
    speech_path = escape_ps_single_quotes(str(speech_script_path))
    wav_path = escape_ps_single_quotes(str(output_path))
    voice = escape_ps_single_quotes(voice_name)
    script = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$items = Get-Content -Raw -Encoding UTF8 -LiteralPath '__SPEECH_PATH__' | ConvertFrom-Json
if (-not $items) { exit 0 }

function Escape-Ssml([string]$value) {
  return [System.Security.SecurityElement]::Escape($value)
}

function Split-Sentences([string]$text) {
  if ([string]::IsNullOrWhiteSpace($text)) { return @() }
  $clean = ($text -replace '\r\n', ' ' -replace '\r', ' ' -replace '\n', ' ')
  $parts = [regex]::Split($clean, '(?<=[\u3002\uFF1F\uFF01!?；;])\s*')
  $sentences = @()
  foreach ($part in $parts) {
    $trimmed = $part.Trim()
    if ($trimmed) { $sentences += $trimmed }
  }
  if ($sentences.Count -eq 0 -and $clean.Trim()) { $sentences = @($clean.Trim()) }
  return $sentences
}

function Get-StyleProfile([string]$style) {
  switch ($style) {
    'warm' { return @{ rate = '-3%'; pitch = '+1st' } }
    'gentle' { return @{ rate = '-6%'; pitch = '+1st' } }
    'encouraging' { return @{ rate = '-1%'; pitch = '+2st' } }
    'careful' { return @{ rate = '-8%'; pitch = '-1st' } }
    default { return @{ rate = '__DEFAULT_RATE__%'; pitch = '0st' } }
  }
}

function Build-Ssml([object[]]$speechItems) {
  $body = New-Object System.Text.StringBuilder
  [void]$body.AppendLine("<speak version='1.0' xml:lang='zh-CN'>")
  [void]$body.AppendLine("<voice name='__VOICE_NAME__'>")
  foreach ($item in @($speechItems)) {
    $style = 'clear'
    if ($item.voice -and $item.voice.style) { $style = [string]$item.voice.style }
    $profile = Get-StyleProfile $style
    $text = [string]$item.text
    $sentences = Split-Sentences $text
    if ($sentences.Count -eq 0) { continue }
    [void]$body.AppendLine('<p>')
    [void]$body.AppendLine("<prosody rate='" + $profile.rate + "' pitch='" + $profile.pitch + "'>")
    for ($i = 0; $i -lt $sentences.Count; $i++) {
      $sentence = Escape-Ssml $sentences[$i]
      $sentence = $sentence.Replace(([char]0xFF0C).ToString(), "<break time='120ms' />")
      $sentence = $sentence.Replace(',', "<break time='100ms' />")
      if ($sentence) { [void]$body.Append($sentence) }
      if ($i -lt $sentences.Count - 1) {
        [void]$body.Append("<break time='180ms' />")
      }
    }
    [void]$body.AppendLine('</prosody>')
    $pause = 0
    if ($item.voice -and $item.voice.pause_after_ms) { $pause = [int]$item.voice.pause_after_ms }
    if ($pause -gt 0) { [void]$body.AppendLine("<break time='" + $pause + "ms' />") } else { [void]$body.AppendLine("<break time='240ms' />") }
    [void]$body.AppendLine('</p>')
  }
  [void]$body.AppendLine('</voice>')
  [void]$body.AppendLine('</speak>')
  return $body.ToString()
}

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $synth.SelectVoice('__VOICE_NAME__') } catch { }
$synth.Rate = __RATE__
$synth.Volume = __VOLUME__
$ssml = Build-Ssml $items
$synth.SetOutputToWaveFile('__WAV_PATH__')
$synth.SpeakSsml($ssml)
$synth.Dispose()
""".strip()
    return (
        script.replace("__SPEECH_PATH__", speech_path)
        .replace("__WAV_PATH__", wav_path)
        .replace("__VOICE_NAME__", voice)
        .replace("__RATE__", str(int(rate)))
        .replace("__VOLUME__", str(int(volume)))
    )


def build_edge_text(speech_items: list[dict]) -> str:
    segments: list[str] = []
    for item in speech_items:
        text = normalize_edge_text(str((item or {}).get("text", "")))
        if not text:
            continue
        if text[-1] not in "。！？!?；;":
            text += "。"
        segments.append(text)
    return "\\n\\n".join(segments)


def normalize_edge_text(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("\\r\\n", "\\n").replace("\\r", "\\n")
    text = " ".join(part.strip() for part in text.splitlines() if part.strip())
    text = " ".join(text.split())
    return text.strip()


def edge_tts_available() -> bool:
    return importlib.util.find_spec("edge_tts") is not None


def env_text(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def escape_ps_single_quotes(value: str) -> str:
    return value.replace("'", "''")
