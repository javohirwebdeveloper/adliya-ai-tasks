"""Qalqonning veb-sahifasi va API si. Matn hech qayerda saqlanmaydi va jurnalga yozilmaydi.

  POST /api/mask    {"text": "..."}              -> {"masked": "...", "key": {"[ISM_1]": "..."}, "found": [...]}
  POST /api/unmask  {"text": "...", "key": {...}} -> {"text": "..."}
  GET  /api/namunalar                             -> Gemma 4 ning oldindan yozib olingan haqiqiy javoblari
"""
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from shield import Shield

app = FastAPI(title="Shaxsiy ma'lumot qalqoni", version="1.0")
S = Shield()
EXAMPLES = Path(__file__).with_name("namunalar.json")
NAMUNA = json.loads(EXAMPLES.read_text(encoding="utf-8")) if EXAMPLES.exists() else []


class MaskIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class UnmaskIn(BaseModel):
    text: str = Field(max_length=20000)
    key: dict[str, str]


@app.post("/api/mask")
def mask(body: MaskIn):
    t = time.perf_counter()
    masked, key = S.mask(body.text)
    found = [{"tur": k, "qiymat": body.text[s:e]} for k, s, e in S.detect(body.text)]
    return {"masked": masked, "key": key, "found": found, "ms": round((time.perf_counter() - t) * 1000, 2)}


@app.post("/api/unmask")
def unmask(body: UnmaskIn):
    if len(body.key) > 500:
        raise HTTPException(413, "kalit juda katta")
    return {"text": Shield.unmask(body.text, body.key)}


@app.get("/api/namunalar")
def namunalar():
    return NAMUNA


@app.get("/health")
def health():
    return {"ok": True}


PAGE = """<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shaxsiy ma'lumot qalqoni</title><meta name="robots" content="noindex">
<style>
:root{--b:#0f2a4a;--m:#64748b;--l:#e2e8f0;--a:#2f6fed}*{box-sizing:border-box}
body{margin:0;font:16px/1.55 system-ui,"Segoe UI",sans-serif;color:var(--b);background:#f4f7fb}
main{max-width:1100px;margin:0 auto;padding:28px 18px 60px}h1{font-size:28px;margin:0 0 4px}
.sub{color:var(--m);margin:0 0 20px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--l);border-radius:16px;padding:18px}
textarea{width:100%;min-height:230px;border:1px solid var(--l);border-radius:12px;padding:12px;font-family:inherit;font-size:15px;line-height:1.5;resize:vertical}
button{background:var(--a);color:#fff;border:0;border-radius:10px;padding:11px 18px;font-weight:600;cursor:pointer;margin:10px 8px 0 0}
button.g{background:#eef2f7;color:var(--b)}h2{font-size:17px;margin:0 0 10px}
.out{white-space:pre-wrap;min-height:120px}.tag{border-radius:6px;padding:1px 6px;font-weight:600;font-size:14px}
table{width:100%;border-collapse:collapse;font-size:14px;margin-top:10px}td{border-top:1px solid var(--l);padding:6px 4px;vertical-align:top}
.note{color:var(--m);font-size:13px;margin-top:10px}.lbl{color:var(--m);font-size:13px;font-weight:600;margin-bottom:4px}#g4 .out{min-height:0}
</style></head><body><main>
<h1>Shaxsiy ma'lumot qalqoni</h1>
<p class="sub">Matn sun'iy intellektga yuborilishidan oldin ism, pasport, JSHSHIR, telefon, karta, manzil kabi ma'lumotlar yashiriladi.
AI javobi qaytgach, ular joyiga qo'yiladi. Lotin, kirill va rus tilida ishlaydi. Matn saqlanmaydi.</p>
<div class="grid"><div class="card"><h2>1. Asl matn</h2>
<textarea id="t">Assalomu alaykum. Men Karimov Akmal Rustam o'g'li, pasport AB4567123, JSHSHIR 31505901234567.
Toshkent shahri, Chilonzor tumani, Bunyodkor ko'chasi, 12-uy, 45-xonadonda yashayman. Tel: +998 90 123 45 67.
Uzcard kartamga (8600 1234 5678 9012) 05.09.2026 da to'langan davlat boji qaytarilmadi.</textarea>
<button id="go">Yashirish</button><button class="g" id="ex">Boshqa misol</button>
<div class="note" id="ms"></div></div>
<div class="card"><h2>2. AI ko'radigan matn</h2><div class="out" id="m"></div>
<table id="k"></table></div></div>
<div class="card" style="margin-top:18px"><h2>3. AI javobi asl ma'lumot bilan qaytariladi</h2>
<div class="out" id="r"></div><div class="note">Bu yerda AI javobini namuna sifatida qo'lda yozdik: unda faqat [ISM_1] kabi belgilar bor, qalqon ularni qaytaradi.
Haqiqiy model javoblari pastda.</div></div>
<div class="card" id="g4" style="margin-top:18px;display:none"><h2>4. Gemma 4 ning haqiqiy javoblari</h2>
<div id="gb"></div><div class="grid" style="margin-top:12px"><div><div class="lbl">Fuqaro yozgan murojaat</div><div class="out" id="ga"></div></div>
<div><div class="lbl">Gemma ko'rgan matn</div><div class="out" id="gm"></div></div></div>
<div class="lbl" style="margin-top:14px">Gemma javobi</div><div class="out" id="gj"></div>
<div class="lbl" style="margin-top:14px">Fuqaroga boradi</div><div class="out" id="gf"></div>
<div class="note">Oldindan yozib olingan: Gemma 4 12B, lokal model (Modal GPU). Model faqat "Gemma ko'rgan matn" ni ko'rgan.
Murojaat va undagi shaxsiy ma'lumotlarni ham Gemma to'qib chiqargan, ular haqiqiy odamga tegishli emas.</div></div>
</main><script>
const C={ISM:'#dbeafe',PASPORT:'#fde68a',JSHSHIR:'#fecaca',TELEFON:'#bbf7d0',KARTA:'#fbcfe8',HISOB:'#fbcfe8',STIR:'#e9d5ff',
EMAIL:'#bae6fd',MANZIL:'#fed7aa',AVTO:'#e5e7eb',TUG_SANA:'#ddd6fe',HUJJAT:'#fde68a',RAQAM:'#fecaca'};
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const paint=s=>esc(s).replace(/\\[([A-Z_]+)_(\\d+)\\]/g,(m,k)=>'<span class="tag" style="background:'+(C[k]||'#eee')+'">'+m+'</span>');
const EX=[`Добрый день. Меня зовут Петрова Анна Сергеевна, паспорт AC 2345678, ИНН 412345678. Мой номер +998 (90) 765-43-21. Прошу вернуть госпошлину.`,
`Аризачи Тўхтасинова Мадина Илҳом қизи, ЖШШИР 41505923400017, Наманган вилояти, Чуст тумани, Ғалаба маҳалласи, 3-уй. Нотариал ишончнома бекор қилинсин.`,
`salom aka, men Dilshod, pasport aa 1234567. mashinam 01 A 777 AA, prava muddati o'tibdi. tel 901112233`];let ei=0;
async function go(){const res=await fetch('api/mask',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({text:t.value})});
const d=await res.json();m.innerHTML=paint(d.masked);ms.textContent=d.found.length+' ta shaxsiy ma\\'lumot topildi, '+d.ms+' ms';
k.innerHTML=Object.entries(d.key).map(([a,b])=>'<tr><td>'+paint(a)+'</td><td>'+esc(b)+'</td></tr>').join('');
const ism=Object.keys(d.key).find(x=>x.startsWith('[ISM'));const ans='Hurmatli '+(ism||'fuqaro')+'! Murojaatingiz qabul qilindi. Javob '
+(Object.keys(d.key).find(x=>x.startsWith('[TELEFON'))||'telefon')+' raqamiga SMS orqali yuboriladi.';
const u=await fetch('api/unmask',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({text:ans,key:d.key})});
r.innerHTML='<b>AI javobi:</b> '+paint(ans)+'<br><b>Fuqaroga boradi:</b> '+esc((await u.json()).text)}
const LBL={"o'zbek lotin":'Lotin',"o'zbek kirill":'Кирилл','rus tili':'Русский'};
function show(g,i){const x=g[i];ga.textContent=x.asl;gm.innerHTML=paint(x.yashirin);
gj.innerHTML='<b>Mavzu:</b> '+esc(x.mavzu)+(x.shoshilinch?' · <b>shoshilinch</b>':'')+'<br><b>Xulosa:</b> '+paint(x.xulosa)+'<br><b>Javob loyihasi:</b> '+paint(x.javob);
gf.textContent=x.fuqaroga;gb.querySelectorAll('button').forEach((b,j)=>b.className=j==i?'':'g')}
fetch('api/namunalar').then(r=>r.json()).then(g=>{if(!g.length)return;g4.style.display='';
gb.innerHTML=g.map((x,i)=>'<button data-i="'+i+'">'+(LBL[x.yozuv]||x.yozuv)+'</button>').join('');
gb.querySelectorAll('button').forEach(b=>b.onclick=()=>show(g,+b.dataset.i));show(g,0)});
document.getElementById('go').onclick=go;document.getElementById('ex').onclick=()=>{t.value=EX[ei++%EX.length];go()};go();
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def page():
    return PAGE
