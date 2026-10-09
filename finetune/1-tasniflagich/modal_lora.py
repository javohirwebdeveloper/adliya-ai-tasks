# lora_demo.py ni Modal GPU'da (L4) ishga tushiradi: server protsessori band bo'lmaydi.
# Narx: L4 $0,80/soat; ish 20 daqiqadan oshsa, o'zi to'xtaydi (eng ko'pi ~$0,27).
import io
import json
import zipfile
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("torch==2.5.1", "transformers>=4.46,<5", "peft>=0.13", "scikit-learn", "numpy",
                      "sentencepiece", "protobuf")
         .add_local_dir(str(ROOT / "task1-faq/data"), "/w/data")
         .add_local_file(str(ROOT / "task1-faq/eval/test_queries.csv"), "/w/eval/test_queries.csv")
         .add_local_file(str(ROOT / "task1-faq/eval/final_test_queries.csv"), "/w/eval/final_test_queries.csv")
         .add_local_file(str(HERE / "lora_demo.py"), "/w/lora_demo.py"))
app = modal.App("adliya-lora-demo", image=image)


@app.function(gpu="L4", timeout=20 * 60)
def train(epochs: int = 3) -> bytes:
    import os
    import runpy
    os.environ["EPOCHS_RUN"] = str(epochs)
    os.environ.update({"DATA_DIR": "/w", "OUT_DIR": "/tmp/natija", "THREADS": "4", "EPOCHS": os.environ.get("EPOCHS_RUN", "3")})
    runpy.run_path("/w/lora_demo.py", run_name="__main__")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in Path("/tmp/natija").rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to("/tmp/natija"))
    return buf.getvalue()


@app.local_entrypoint()
def main():
    import os
    ep = int(os.environ.get("EPOCHS", "3"))
    data = train.remote(ep)
    out = HERE / "natija"
    out.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(out)
    print("NATIJA:", json.dumps(json.load(open(out / "natija.json")), ensure_ascii=False))
