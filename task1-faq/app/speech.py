"""Ovozli savolni matnga aylantirish (internetsiz, oddiy protsessorda).

Model STT_MODEL bilan tanlanadi (modellar eval/stt_bench.py da solishtirilgan, natijasi README da):
  gigaam-multilingual-ctc    onnx-asr nomi bilan (model HF keshidan olinadi)
  <tur yoki nom>:<HF repo>   masalan nemo-conformer-ctc:OpenVoiceOS/stt_uz_fastconformer_hybrid_large_pc_onnx
  vosk                       eski variant, VOSK_MODEL papkasidagi Kaldi modeli
STT_QUANT=int8 bo'lsa 8 bitli fayl ishlatiladi (xotira 3 barobar kam, aniqlik biroz pastroq).
"""
import json
import os
import subprocess
import tempfile
import threading
from pathlib import Path

import numpy as np

SR = 16000
MAX_SECONDS = 60


def decode(data: bytes) -> np.ndarray:
    """Istalgan formatdagi ovoz (Telegram ogg/opus, brauzer webm, mp3, m4a) -> 16 kHz mono float32."""
    with tempfile.NamedTemporaryFile(suffix=".audio") as f:     # m4a kabi formatlarni quvur orqali o'qib bo'lmaydi
        f.write(data)
        f.flush()
        pcm = subprocess.run(["ffmpeg", "-v", "quiet", "-i", f.name, "-t", str(MAX_SECONDS), "-ar", str(SR), "-ac", "1",
                              "-f", "s16le", "-"], capture_output=True, timeout=30).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


def split_long(a: np.ndarray, max_s: float = 20.0, search_s: float = 6.0) -> list[np.ndarray]:
    """Modellar 25 soniyagacha bo'lgan gaplarda o'qitilgan. Uzun xabar ~20 s li bo'laklarga, so'z o'rtasidan
    emas, oxirgi 6 soniyadagi eng jim joyidan bo'linadi."""
    out, start, max_n, win = [], 0, int(max_s * SR), int(0.1 * SR)
    while len(a) - start > max_n:
        lo = start + max_n - int(search_s * SR)
        seg = a[lo:start + max_n].astype(np.float64)
        e = np.cumsum(np.concatenate([[0.0], seg * seg]))
        cut = lo + int(np.argmin(e[win:] - e[:-win])) + win // 2
        out.append(a[start:cut])
        start = cut
    out.append(a[start:])
    return out


def model_dir(repo: str) -> str:
    """HF keshidagi model papkasi. Og'irliklar alohida faylda (.onnx.data) bo'lsa, onnxruntime keshning boshqa
    joyiga ishora qiluvchi symlink orqali uni o'qishdan bosh tortadi (xavfsizlik tekshiruvi). Shunda fayllar
    bitta papkaga hardlink qilib yig'iladi: joy egallamaydi."""
    from huggingface_hub import snapshot_download
    src = Path(snapshot_download(repo))
    if not any(src.glob("*.onnx.data")):
        return str(src)
    dst = src.parent.parent / "linked"
    dst.mkdir(exist_ok=True)
    for f in src.iterdir():
        if not (dst / f.name).exists():
            os.link(f.resolve(), dst / f.name)
    return str(dst)


class Speech:
    def __init__(self, model: str, quantization: str | None = None, threads: int = 4):
        self.name = model + (f" ({quantization})" if quantization else "")
        self._lock = threading.Lock()            # bir vaqtda bitta xabar: protsessor yadrolari talashmaydi
        if model == "vosk":
            from vosk import Model, SetLogLevel
            SetLogLevel(-1)
            self._vosk = Model(os.environ["VOSK_MODEL"])
            self._run = self._run_vosk
            return
        import onnx_asr
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads, so.inter_op_num_threads = threads, 1
        path = None
        if ":" in model:
            model, repo = model.split(":", 1)
            path = model_dir(repo)
        self._onnx = onnx_asr.load_model(model, path, quantization=quantization or None, sess_options=so)
        self._run = lambda a: self._onnx.recognize(a, sample_rate=SR)

    def _run_vosk(self, a: np.ndarray) -> str:
        from vosk import KaldiRecognizer
        rec = KaldiRecognizer(self._vosk, SR)
        rec.AcceptWaveform(np.clip(a * 32768, -32768, 32767).astype(np.int16).tobytes())
        return json.loads(rec.FinalResult()).get("text", "")

    def recognize(self, a: np.ndarray) -> str:
        if len(a) < SR // 4:                     # chorak soniyadan qisqa: tugma tasodifan bosilgan
            return ""
        with self._lock:
            parts = [self._run(c).strip() for c in split_long(a)]
        text = " ".join(p for p in parts if p)
        return text[:1].upper() + text[1:]                  # GigaAM kichik harf bilan yozadi; gap boshi bosh harf

    def transcribe(self, data: bytes) -> str:
        return self.recognize(decode(data))


def load_speech(threads: int = 4) -> Speech | None:
    model = os.getenv("STT_MODEL", "").strip()
    if not model or (model == "vosk" and not os.path.isdir(os.getenv("VOSK_MODEL", ""))):
        return None
    sp = Speech(model, os.getenv("STT_QUANT", "").strip() or None, threads)
    sp.recognize(np.random.default_rng(0).normal(0, 0.01, SR).astype(np.float32))     # isitish
    return sp
