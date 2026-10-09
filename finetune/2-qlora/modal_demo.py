# O'qitilgan modelning jonli demosi (Modal GPU, L4 $0,80/soat). Bitta gapga ikki javob qaytaradi:
#   oldin  - asosiy Qwen3-4B (LoRA adapteri o'chirilgan)
#   keyin  - o'sha model + biz o'qitgan QLoRA adapteri
# 5 daqiqa so'rov bo'lmasa o'zi o'chadi; bir vaqtda faqat 1 ta GPU. Kirish maxfiy kalit bilan.
#
#   TRENING_TOKEN=... modal deploy modal_demo.py
import os
from pathlib import Path

import modal

HERE = Path(__file__).parent
MODEL = "Qwen/Qwen3-4B-Instruct-2507"
SYSTEM = "Sen rasmiy hujjatlardagi topshiriq gapidan ijrochi va muddatni ajratuvchi yordamchisan. Faqat JSON qaytar."
INSTR = ('Quyidagi topshiriq gapidan ijrochi(lar)ni va muddatni ajrat. JSON shakli: {"ijrochi": [ro\'yxat], '
         '"muddat": "gapdagi muddat iborasi yoki null", "muddat_turi": "sana | nisbiy | davriy | boshlanish | doimiy | yo\'q"}'
         "\nGap: ")

image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("torch==2.5.1", "transformers>=4.51,<5", "peft>=0.13", "bitsandbytes>=0.45", "accelerate>=1.0",
                      "fastapi[standard]")
         .env({"HF_HOME": "/cache"})
         .add_local_dir(str(HERE / "natija" / "adapter"), "/w/adapter"))
app = modal.App("adliya-trening", image=image)
cache = modal.Volume.from_name("adliya-hf-cache", create_if_missing=True)      # model har safar qayta yuklanmasin
secret = modal.Secret.from_dict({"TRENING_TOKEN": os.environ.get("TRENING_TOKEN", "")})


@app.cls(gpu="L4", scaledown_window=300, max_containers=1, timeout=180, volumes={"/cache": cache}, secrets=[secret])
class Model:
    @modal.enter()
    def load(self):
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(MODEL)
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16,
                                 bnb_4bit_use_double_quant=True)
        base = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=bnb, device_map={"": 0},
                                                    torch_dtype=torch.bfloat16)
        self.model = PeftModel.from_pretrained(base, "/w/adapter")
        self.model.eval()
        cache.commit()

    def generate(self, text: str) -> str:
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": INSTR + text}]
        prompt = self.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        enc = self.tok(prompt, return_tensors="pt").to("cuda")
        with self.torch.no_grad():
            out = self.model.generate(**enc, max_new_tokens=160, do_sample=False, pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    @modal.fastapi_endpoint(method="POST")
    def tahlil(self, body: dict):
        import json
        import re
        import time
        from fastapi import HTTPException
        if not os.environ.get("TRENING_TOKEN") or body.get("token") != os.environ["TRENING_TOKEN"]:
            raise HTTPException(403, "ruxsat yo'q")
        text = str(body.get("text") or "").strip()[:600]
        if not text:
            raise HTTPException(400, "gap bo'sh")

        def parse(raw):
            m = re.search(r"\{.*\}", raw, re.S)
            try:
                return json.loads(m.group(0)) if m else None
            except json.JSONDecodeError:
                return None

        res = {}
        for name in ("oldin", "keyin"):
            t = time.perf_counter()
            if name == "oldin":
                with self.model.disable_adapter():               # o'qitilgan qismsiz: asosiy model
                    raw = self.generate(text)
            else:
                raw = self.generate(text)
            res[name] = {"raw": raw[:800], "json": parse(raw), "ms": int((time.perf_counter() - t) * 1000)}
        return res
