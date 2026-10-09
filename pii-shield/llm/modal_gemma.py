# Gemma 4 (lokal model, Modal GPU'da) bilan ikki ish:
#   1. Mustaqil sinov matnlari: 9 mavzuda fuqaro murojaatlari va ulardagi shaxsiy ma'lumotlar ro'yxati (qalqonning ko'r testi).
#   2. Murojaat yordamchisi: mavzu, shoshilinchlik, xulosa, javob loyihasi. Asl va yashirilgan matnda alohida,
#      natijasini solishtirish uchun (maxfiylik tushunishni buzadimi?).
# Narx: L40S $1,95/soat; 30 daqiqadan oshsa o'zi to'xtaydi.
import json
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
MODEL = "google/gemma-4-12B-it"
image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("vllm>=0.11", "huggingface_hub[hf_transfer]")
         .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "VLLM_USE_FLASHINFER_SAMPLER": "0"})   # nvcc yo'q: FlashInfer namuna olish yadrosi kompilyatsiya qilinmaydi
         .add_local_dir(str(HERE.parent / "shield"), "/w/shield")
         .add_local_file(str(HERE / "prompts.py"), "/w/prompts.py"))
app = modal.App("adliya-gemma", image=image)


@app.function(gpu="L40S", timeout=30 * 60)
def run(n_per_topic: int = 7, seed: int = 11, sample_seed: int = 7) -> str:
    import sys
    sys.path.insert(0, "/w")
    import prompts
    from shield import Shield
    from vllm import LLM, SamplingParams

    llm = LLM(MODEL, max_model_len=4096, gpu_memory_utilization=0.9)
    chat = lambda msgs, sp: [o.outputs[0].text for o in llm.chat([[{"role": "user", "content": m}] for m in msgs], sp)]

    # 1. sinov matnlari
    jobs = prompts.generation_jobs(n_per_topic, seed)
    raw = chat([j["prompt"] for j in jobs], SamplingParams(temperature=0.9, top_p=0.95, max_tokens=900, seed=sample_seed))
    items = []
    for j, r in zip(jobs, raw):
        d = prompts.parse_json(r)
        if d and isinstance(d.get("matn"), str):
            items.append({"mavzu": j["topic"], "uslub": j["style"], "yozuv": j["script"], "matn": d["matn"],
                          "shaxsiy": d.get("shaxsiy") or []})

    # 2. yordamchi: asl va yashirilgan matnda
    sh = Shield()
    for it in items:
        it["masked"], it["key"] = sh.mask(it["matn"])
    sp = SamplingParams(temperature=0.0, max_tokens=700)
    out_orig = chat([prompts.assistant_prompt(it["matn"]) for it in items], sp)
    out_mask = chat([prompts.assistant_prompt(it["masked"]) for it in items], sp)
    for it, a, b in zip(items, out_orig, out_mask):
        it["javob_asl"], it["javob_yashirin"] = prompts.parse_json(a), prompts.parse_json(b)
        it["javob_yashirin_xom"] = b[:1500]
    return json.dumps(items, ensure_ascii=False)


@app.local_entrypoint()
def main(n: int = 7, seed: int = 11, sample_seed: int = 7, out: str = "gemma_items.json"):
    # 1-to'plam: standart qiymatlar. 2-to'plam (qoidalar tuzatilgandan keyin, hech ko'rilmagan):
    #   modal run modal_gemma.py --n 10 --seed 23 --sample-seed 29 --out gemma_items_v2.json
    folder = HERE / "natija"
    folder.mkdir(exist_ok=True)
    data = run.remote(n, seed, sample_seed)
    (folder / out).write_text(data)
    print("tayyor:", len(json.loads(data)), "ta murojaat")
