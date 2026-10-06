"""Ovozni matnga aylantirish (STT) modellarini solishtirish: aniqlik va oddiy protsessordagi tezlik.

Bot avval Vosk ning kichik o'zbekcha modelini ishlatardi. U "pravamning muddati tugadi" ni "radarning
muddati tugadi" deb eshitdi. Shuning uchun ochiq modellar bir xil sharoitda solishtirildi:

  vosk          alphacep/vosk-model-small-uz-0.22, Kaldi, 49 MB (avvalgi)
  gigaam        ai-sage/GigaAM-Multilingual, ctc, 220M parametr, ONNX (onnx-asr)
  gigaam-large  ai-sage/GigaAM-Multilingual, large_ctc, 585M, ONNX
  nvidia        nvidia/stt_uz_fastconformer_hybrid_large_pc, 115M, ONNX
  kotib         Kotib/uzbek_stt_v1, Whisper-medium asosida, 769M, transformers
  *-int8        o'sha model 8 bitli ko'rinishda (fayli 4 barobar kichik). NVIDIA modelining int8 fayli
                bo'sh matn qaytaradi (eksport buzuq), shuning uchun u ro'yxatda yo'q

To'plamlar:
  fleurs  Google FLEURS o'zbekcha test qismidan tasodifiy N ta gap (haqiqiy odamlar o'qigan)
  dir     papkadagi ovozli xabarlar; yonida refs.tsv bo'lsa (fayl<TAB>to'g'ri matn) xato foizi ham hisoblanadi

Har bir model alohida jarayonda ishlaydi: xotira toza o'lchanadi, modellar bir-biriga xalaqit bermaydi.
Hamma modelga bir xil CPU oqimlari soni (TORCH_THREADS) beriladi, birinchi (isitish) ishga tushirish
hisobga olinmaydi. "3 s" ustuni: botga keladigan odatiy qisqa savol uzunligidagi bo'lakni o'qish vaqti.

  python eval/stt_bench.py fleurs --dir /data/fleurs/uz_uz --n 150 --out eval/stt_fleurs
  python eval/stt_bench.py dir --dir voices/ --models vosk,gigaam --out /tmp/voices_bench
  python eval/stt_bench.py report --out eval/stt_fleurs        # alohida o'lchangan modellarni bitta jadvalga
"""
import argparse
import csv
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.normalize import cyr_to_lat, normalize  # noqa: E402
from app.speech import model_dir  # noqa: E402

SR = 16000
THREADS = int(os.getenv("TORCH_THREADS", "6"))
AUDIO_EXT = {".ogg", ".oga", ".opus", ".wav", ".mp3", ".m4a", ".flac", ".webm"}
NVIDIA_REPO = "OpenVoiceOS/stt_uz_fastconformer_hybrid_large_pc_onnx"
GIGAAM_REPO = "istupakov/gigaam-multilingual-ctc-onnx"                 # onnx-asr ham shu repolardan oladi
GIGAAM_LARGE_REPO = "istupakov/gigaam-multilingual-large-ctc-onnx"
ALL = ["vosk", "gigaam", "gigaam-int8", "gigaam-large", "gigaam-large-int8", "nvidia", "kotib"]


def load_audio(path) -> np.ndarray:
    pcm = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(path), "-ar", str(SR), "-ac", "1", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


def norm(text: str) -> str:
    """Solishtirish uchun: kichik harf, apostroflar bir xil, tinish belgilarisiz, kirill lotinga."""
    t = cyr_to_lat(normalize(text)).lower()
    t = re.sub(r"[^\w' ]+", " ", t)
    t = re.sub(r"(?<![^\W\d_])'", " ", t)          # harfdan keyin kelmagan apostrof (qo'shtirnoq) olib tashlanadi
    return re.sub(r"\s+", " ", t).strip()


# --- modellar: har biri "audio (16 kHz float32) -> matn" funksiyasini qaytaradi ---

def _vosk():
    from vosk import KaldiRecognizer, Model, SetLogLevel
    SetLogLevel(-1)
    model = Model(os.environ.get("VOSK_MODEL", "/models/vosk-model-small-uz-0.22"))

    def run(a):
        rec = KaldiRecognizer(model, SR)
        rec.AcceptWaveform(np.clip(a * 32768, -32768, 32767).astype(np.int16).tobytes())
        return json.loads(rec.FinalResult()).get("text", "")
    return run


def _onnx(name, repo=None, quant=None):
    def load():
        import onnx_asr
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads, so.inter_op_num_threads = THREADS, 1
        model = onnx_asr.load_model(name, model_dir(repo) if repo else None, quantization=quant, sess_options=so)
        return lambda a: model.recognize(a, sample_rate=SR)
    return load


def _kotib():
    import torch
    torch.set_num_threads(THREADS)
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    proc = WhisperProcessor.from_pretrained("Kotib/uzbek_stt_v1")
    model = WhisperForConditionalGeneration.from_pretrained("Kotib/uzbek_stt_v1").eval()

    def run(a):
        x = proc(a, sampling_rate=SR, return_tensors="pt").input_features
        with torch.inference_mode():
            ids = model.generate(x, language="uz", task="transcribe", num_beams=1, max_new_tokens=220)
        return proc.batch_decode(ids, skip_special_tokens=True)[0]
    return run


LOADERS = {
    "vosk": _vosk,
    "gigaam": _onnx("gigaam-multilingual-ctc", GIGAAM_REPO),
    "gigaam-int8": _onnx("gigaam-multilingual-ctc", GIGAAM_REPO, quant="int8"),
    "gigaam-large": _onnx("gigaam-multilingual-large-ctc", GIGAAM_LARGE_REPO),
    "gigaam-large-int8": _onnx("gigaam-multilingual-large-ctc", GIGAAM_LARGE_REPO, quant="int8"),
    "nvidia": _onnx("nemo-conformer-ctc", NVIDIA_REPO),
    "kotib": _kotib,
}


def rss_mb(field="VmRSS") -> float:
    for line in open("/proc/self/status"):
        if line.startswith(field + ":"):
            return int(line.split()[1]) / 1024
    return 0.0


def worker(key: str, manifest: str, out: str):
    items = json.load(open(manifest))
    audio = [load_audio(it["path"]) for it in items]
    base = rss_mb()
    t = time.perf_counter()
    run = LOADERS[key]()
    load_s = time.perf_counter() - t
    run(audio[0])                                                  # isitish
    run(audio[0][:3 * SR])
    hyps, secs = [], []
    for a in audio:
        t = time.perf_counter()
        hyps.append(run(a).strip())
        secs.append(time.perf_counter() - t)
    short = [a[:3 * SR] for a in audio if len(a) >= 3 * SR][:20]
    short_secs = []
    for a in short:
        t = time.perf_counter()
        run(a)
        short_secs.append(time.perf_counter() - t)
    json.dump({"model": key, "hyps": hyps, "secs": secs, "short_secs": short_secs, "load_s": load_s,
               "ram_mb": rss_mb("VmHWM") - base, "audio_s": [len(a) / SR for a in audio]},
              open(out, "w"), ensure_ascii=False)


def manifest_fleurs(root: Path, n: int, seed: int):
    rows = list(csv.reader(open(root / "test.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    by_sentence = {}
    for r in rows:                                                 # har bir gapdan bitta yozuv: matnlar takrorlanmasin
        by_sentence.setdefault(r[0], r)
    picked = random.Random(seed).sample(sorted(by_sentence.values()), min(n, len(by_sentence)))
    return [{"id": r[1], "path": str(root / "audio" / "test" / r[1]), "ref": r[2]} for r in picked]


def manifest_dir(root: Path):
    refs = {}
    if (root / "refs.tsv").exists():
        for line in open(root / "refs.tsv", encoding="utf-8"):
            if "\t" in line:
                f, ref = line.rstrip("\n").split("\t", 1)
                refs[f] = ref
    files = sorted(p for p in root.iterdir() if p.suffix.lower() in AUDIO_EXT)
    return [{"id": p.name, "path": str(p), "ref": refs.get(p.name)} for p in files]


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p / 100 * len(xs)))] if xs else 0.0


def summarize(res, items):
    import jiwer
    out = {"model": res["model"], "load_s": round(res["load_s"], 1), "ram_mb": round(res["ram_mb"]),
           "rtf": round(sum(res["secs"]) / sum(res["audio_s"]), 4),
           "clip_p50_s": round(pct(res["secs"], 50), 3),
           "short3s_p50_s": round(pct(res["short_secs"], 50), 3), "short3s_p95_s": round(pct(res["short_secs"], 95), 3)}
    pairs = [(norm(it["ref"]), norm(h)) for it, h in zip(items, res["hyps"]) if it.get("ref")]
    if pairs:
        refs, hyps = [p[0] for p in pairs], [p[1] if p[1] else "<bo'sh>" for p in pairs]
        out["wer"] = round(100 * jiwer.wer(refs, hyps), 1)
        out["cer"] = round(100 * jiwer.cer(refs, hyps), 1)
        nd = [(r, h) for r, h in zip(refs, hyps) if not re.search(r"\d", r)]
        out["wer_no_digits"] = round(100 * jiwer.wer([r for r, _ in nd], [h for _, h in nd]), 1) if nd else None
        out["n_no_digits"] = len(nd)
    return out


def report(out: Path) -> list[dict]:
    """Papkadagi barcha model natijalarini (_<model>.json) bitta jadvalga yig'adi."""
    items = json.loads((out / "manifest.json").read_text())
    rows, hyps = [], {it["id"]: {"ref": it.get("ref")} for it in items}
    for key in ALL:
        part = out / f"_{key}.json"
        if not part.exists():
            continue
        res = json.loads(part.read_text())
        rows.append(summarize(res, items))
        for it, h in zip(items, res["hyps"]):
            hyps[it["id"]][key] = h
    (out / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    (out / "hyps.json").write_text(json.dumps(hyps, ensure_ascii=False, indent=1))
    lines = ["| Model | WER % | CER % | WER % (raqamsiz gaplar) | 3 s ovoz, s | RTF | Xotira, MB |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['model']} | {r.get('wer', '-')} | {r.get('cer', '-')} | {r.get('wer_no_digits', '-')} | "
                     f"{r['short3s_p50_s']} | {r['rtf']} | {r['ram_mb']} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["fleurs", "dir", "report", "_worker"])
    ap.add_argument("--dir")
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--models", default="all")
    ap.add_argument("--out")
    ap.add_argument("--key")
    ap.add_argument("--manifest")
    a = ap.parse_args()
    if a.mode == "_worker":
        return worker(a.key, a.manifest, a.out)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.mode == "report":
        return print((out / "summary.md").read_text() if report(out) else "natija yo'q")
    if not (out / "manifest.json").exists():                       # qayta ishga tushirishda to'plam o'zgarmaydi
        items = manifest_fleurs(Path(a.dir), a.n, a.seed) if a.mode == "fleurs" else manifest_dir(Path(a.dir))
        (out / "manifest.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
    items = json.loads((out / "manifest.json").read_text())
    for key in ALL if a.models == "all" else a.models.split(","):
        part = out / f"_{key}.json"
        t = time.time()
        p = subprocess.run([sys.executable, __file__, "_worker", "--key", key, "--manifest", str(out / "manifest.json"),
                            "--out", str(part)], capture_output=True, text=True)
        if p.returncode != 0:
            print(key, "XATO:", p.stderr.strip().splitlines()[-1:] if p.stderr else "", flush=True)
            continue
        print(json.dumps(summarize(json.loads(part.read_text()), items), ensure_ascii=False),
              f"({time.time() - t:.0f} s)", flush=True)
    report(out)


if __name__ == "__main__":
    main()
