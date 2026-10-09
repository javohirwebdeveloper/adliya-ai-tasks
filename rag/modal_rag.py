# 2-qadam (Modal GPU, shu serverda emas): Gemma 4 har savolga ikki xil javob yozadi:
#   rag    faqat 1-topshiriq bazasidan topilgan 3 ta manbaga tayanib, manbasini ko'rsatib
#   yopiq  manbasiz, o'zi bilganidan (solishtirish uchun)
# keyin hakam (yana Gemma) bazada bor savollardagi javoblarni rasmiy javob bilan solishtiradi.
# Qo'shimcha: har xabardan qidiruv uchun toza savol (query rewriting), qidiruv keyin serverda o'lchanadi.
# Gemma faqat qalqondan o'tgan matnni ko'radi. Kirish: natija/inputs.json, chiqish: natija/gemma_rag.json
# Narx: L40S $1,95/soat, bir ishga ~10 daqiqa (~$0,35); 30 daqiqadan oshsa o'zi to'xtaydi.
import json
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
MODEL = "google/gemma-4-12B-it"
image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("vllm>=0.11", "huggingface_hub[hf_transfer]")
         .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "VLLM_USE_FLASHINFER_SAMPLER": "0"})
         .add_local_file(str(HERE / "prompts.py"), "/w/prompts.py"))
app = modal.App("adliya-rag", image=image)


@app.function(gpu="L40S", timeout=30 * 60)
def run(items_json: str) -> str:
    import sys
    sys.path.insert(0, "/w")
    import prompts
    from vllm import LLM, SamplingParams

    items = json.loads(items_json)
    llm = LLM(MODEL, max_model_len=4096, gpu_memory_utilization=0.9)
    sp = SamplingParams(temperature=0.0, max_tokens=600)
    chat = lambda msgs: [o.outputs[0].text for o in llm.chat([[{"role": "user", "content": m}] for m in msgs], sp)]

    rag = chat([prompts.rag_prompt(it["masked"], it["qidiruv"]["items"]) for it in items])
    closed = chat([prompts.closed_prompt(it["masked"]) for it in items])
    for it, a, b in zip(items, rag, closed):
        it["rag"], it["rag_xom"] = prompts.parse_json(a), a[:1500]
        it["yopiq"], it["yopiq_xom"] = prompts.parse_json(b), b[:1500]

    # qidiruv savolini qayta yozish: qidiruvni keyin shu savollar bilan serverda alohida o'lchash uchun
    for it, q in zip(items, chat([prompts.rewrite_prompt(it["masked"]) for it in items])):
        it["qayta_yozilgan"] = q.strip().strip('"').strip()[:500]

    jobs = []
    for i, it in enumerate(items):
        for mode in ("rag", "yopiq"):
            d = it.get(mode) or {}
            if it["tur"] == "bazada" and d.get("javob_bor") and d.get("javob"):
                jobs.append((i, mode, prompts.judge_prompt(it["masked"], it["gold_javob"], d["javob"])))
    for (i, mode, _), v in zip(jobs, chat([j[2] for j in jobs])):
        items[i][mode + "_baho"] = prompts.parse_json(v)
    return json.dumps(items, ensure_ascii=False)


@app.local_entrypoint()
def main():
    data = run.remote((HERE / "natija" / "inputs.json").read_text())
    (HERE / "natija" / "gemma_rag.json").write_text(data)
    print("tayyor:", len(json.loads(data)), "ta savol")
