# qlora_train.py ni Modal GPU'da (L4, $0,80/soat) ishga tushiradi. 40 daqiqadan oshsa o'zi to'xtaydi (eng ko'pi ~$0,55).
import io
import json
import zipfile
from pathlib import Path

import modal

HERE = Path(__file__).parent
image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("torch==2.5.1", "transformers>=4.51,<5", "peft>=0.13", "bitsandbytes>=0.45", "accelerate>=1.0")
         .add_local_dir(str(HERE / "data"), "/w/data")
         .add_local_file(str(HERE / "qlora_train.py"), "/w/qlora_train.py"))
app = modal.App("adliya-qlora", image=image)


@app.function(gpu="L4", timeout=40 * 60)
def run() -> bytes:
    import os
    import runpy
    os.environ.update({"DATA_DIR": "/w/data", "OUT_DIR": "/tmp/out", "SKIP_BEFORE": "1",
                       "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    runpy.run_path("/w/qlora_train.py", run_name="__main__")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for f in Path("/tmp/out").rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to("/tmp/out"))
    return buf.getvalue()


@app.local_entrypoint()
def main():
    out = HERE / "natija"
    out.mkdir(exist_ok=True)
    zipfile.ZipFile(io.BytesIO(run.remote())).extractall(out)
    print("NATIJA:", json.dumps(json.load(open(out / "natija.json")), ensure_ascii=False))
