"""Veb-interfeys: PDF yuklanadi, "Tahlil qilish" bosiladi, rekvizitlar va topshiriqlar chiqadi.

Yonida hujjatning o'zi ko'rinadi: topshiriq yoki rekvizit bosilsa, u hujjatning qayeridan olingani belgilanadi.
Shunda xodim natijani asl hujjat bilan bir qarashda solishtira oladi. Natijani Excel va kalendar (.ics) ga
yuklab olish mumkin. Fayl diskka yozilmaydi va hech qayerga yuborilmaydi.
"""
import pymupdf
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, Response

from .export import to_xlsx
from .pipeline import analyze

MAX_MB = 20
MAX_PAGES = 30

app = FastAPI(title="Hujjat tahlili", version="2.0")


@app.post("/api/analyze")
async def api_analyze(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"Fayl {MAX_MB} MB dan katta")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Bu PDF fayl emas")
    try:
        pages = pymupdf.open(stream=data, filetype="pdf").page_count
    except Exception:
        raise HTTPException(400, "PDF faylni ochib bo'lmadi")
    if pages > MAX_PAGES:
        raise HTTPException(400, f"Hujjat {MAX_PAGES} sahifadan uzun")
    result = await run_in_threadpool(analyze, data)
    result["meta"]["file"] = file.filename
    return result


@app.post("/api/export")
def api_export(result: dict = Body(...)):
    """Tahlil natijasini (JSON) Excel faylga aylantiradi."""
    return Response(to_xlsx(result), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="topshiriqlar.xlsx"'})


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE


PAGE = r"""<!doctype html>
<html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hujjat tahlili</title>
<style>
:root{--bg:#f5f7fa;--card:#fff;--ink:#1c2330;--mut:#5d6778;--line:#e3e8ef;--acc:#1f6feb;--ok:#1a7f37;--warn:#9a6700;--hl:#ffb020}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1320px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:24px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:18px}
.drop{display:block;border:2px dashed #c6cfdb;border-radius:12px;padding:26px;text-align:center;cursor:pointer;transition:.15s}
.drop.on{border-color:var(--acc);background:#eef4ff}.drop b{display:block;font-size:16px;margin-bottom:4px}
.row{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}
button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:10px 18px;font:inherit;font-weight:600;cursor:pointer}
button:disabled{background:#9db8e8;cursor:default}button.ghost{background:#eef1f5;color:var(--ink);font-weight:500}
.fname{color:var(--mut)}.spin{display:none;color:var(--mut)}.spin.on{display:inline}.err{color:#b42318;margin-top:12px}
.grid{display:grid;grid-template-columns:minmax(0,1fr) 440px;gap:18px;align-items:start}
.doc{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow-y:auto;background:#e9edf2;border-radius:12px;padding:10px}
.pg{position:relative;margin-bottom:10px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.12)}.pg img{display:block;width:100%}
.hl{position:absolute;border:2px solid var(--hl);background:rgba(255,176,32,.18);border-radius:3px;pointer-events:none}
.pgn{position:absolute;top:6px;right:8px;font-size:12px;color:var(--mut);background:#fff;border-radius:4px;padding:0 5px}
h2{font-size:17px;margin:0 0 12px}
dl{display:grid;grid-template-columns:170px 1fr;gap:2px 14px;margin:0}dt{color:var(--mut);padding:5px 0}dd{margin:0;padding:5px 6px;border-radius:6px}
dd[data-k]{cursor:pointer}dd[data-k]:hover,tr[data-k]:hover td{background:#f3f7ff}
table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;padding:10px 8px;border-top:1px solid var(--line)}
th{font-size:13px;color:var(--mut);font-weight:600;border-top:0}tr[data-k]{cursor:pointer}tr.sel td,dd.sel{background:#fff6e0}
.chip{display:inline-block;background:#eef4ff;color:#174ea6;border-radius:6px;padding:1px 8px;margin:0 4px 4px 0;font-size:13.5px}
.dl b{display:block}.tag{display:inline-block;font-size:12px;border-radius:5px;padding:0 6px;margin-top:3px;background:#eef1f5;color:var(--mut)}
.tag.sana{background:#e6f4ea;color:var(--ok)}.tag.shartli{background:#fff4d6;color:var(--warn)}
.src{color:var(--mut);font-size:13px;white-space:nowrap}.meta{color:var(--mut);font-size:13.5px}
.warn{background:#fff8e6;border:1px solid #f1d58a;border-radius:8px;padding:10px 12px;margin-top:12px;font-size:14px}
details{margin-top:6px}summary{cursor:pointer;color:var(--mut)}.oth{font-size:14px;margin:6px 0 0;padding-left:18px}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin:-4px 0 14px}
.hint{color:var(--mut);font-size:13px;margin:0 0 10px}
@media (max-width:1000px){.grid{grid-template-columns:1fr}.doc{position:static;max-height:none}}
@media (max-width:700px){dl{grid-template-columns:1fr}dt{padding-bottom:0}
 table,tbody,tr,td{display:block;width:100%}tr.h{display:none}tr{border-top:1px solid var(--line);padding:10px 0}
 td{border:0;padding:3px 0}td.n{font-weight:700}td[data-l]::before{content:attr(data-l);display:block;color:var(--mut);font-size:12.5px}}
</style></head><body><main>
<h1>Hujjat tahlili</h1>
<p class="sub">PDF hujjatdan rekvizitlar va topshiriqlarni ajratadi. Fayl shu serverda tahlil qilinadi va tashqariga yuborilmaydi.</p>
<div class="card">
  <label class="drop" id="drop"><b>PDF faylni shu yerga tashlang yoki bosib tanlang</b>
    <span class="fname" id="fname">Matnli yoki skaner qilingan PDF, 20 MB gacha</span>
    <input type="file" id="file" accept="application/pdf,.pdf" hidden></label>
  <div class="row"><button id="go" disabled>Tahlil qilish</button><span class="spin" id="spin">Tahlil qilinmoqda... skaner bo'lsa 5-15 soniya</span></div>
  <div class="err" id="err"></div>
</div>
<div id="out"></div>
</main>
<script>
const $=id=>document.getElementById(id);let file=null,last=null,BOX={};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt=d=>d?d.split('-').reverse().join('.'):'';
const TYPES={sana:'aniq sana',nisbiy:'hujjat sanasidan',shartli:'shartli',davriy:'davriy',doimiy:'doimiy',boshlanish:'boshlanish sanasi',matn:'matn',"yo'q":"ko'rsatilmagan"};
function pick(f){if(!f)return;file=f;$('fname').textContent=f.name+' · '+(f.size/1024/1024).toFixed(2)+' MB';$('go').disabled=false;$('err').textContent=''}
$('file').onchange=e=>pick(e.target.files[0]);
const drop=$('drop');['dragover','dragenter'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('on')}));
['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('on')}));
drop.addEventListener('drop',e=>pick(e.dataTransfer.files[0]));
$('go').onclick=async()=>{if(!file)return;$('go').disabled=true;$('spin').classList.add('on');$('err').textContent='';$('out').innerHTML='';
 const fd=new FormData();fd.append('file',file);
 try{const r=await fetch('api/analyze',{method:'POST',body:fd});const d=await r.json();
   if(!r.ok)throw new Error(d.detail||'Xatolik');last=d;render(d)}catch(e){$('err').textContent=e.message}
 finally{$('go').disabled=false;$('spin').classList.remove('on')}};
function render(d){const q=d.requisites,m=d.meta;BOX={};
 Object.entries(d.requisite_boxes||{}).forEach(([k,v])=>BOX['r_'+k]=v);d.tasks.forEach(t=>BOX['t'+t.n]=t.boxes||[]);
 const conf=m.ocr_confidence.length?', OCR ishonchi '+m.ocr_confidence.join(' / ')+'%':'';
 let h='<div class="grid"><div><div class="tools"><button class="ghost" id="xlsx">Excel\'ga yuklab olish</button><button class="ghost" id="ics">Muddatlarni kalendarga qo\'shish</button><button class="ghost" id="json">JSON</button></div>';
 h+='<div class="card"><h2>Rekvizitlar</h2><p class="hint">Qatorni bossangiz, hujjatda qayerdan olingani ko\'rsatiladi.</p><dl>';
 const rows=[["Hujjat turi",q.doc_type],["Jo'natuvchi",q.sender,'sender'],["Hujjat raqami",q.number?'№ '+q.number:'','number'],["Sana",fmt(q.date),'date'],
  ["Imzolagan shaxs",q.signatory?(q.signatory+(q.signatory_position?' ('+q.signatory_position+')':'')):'','signatory'],["Kimga",q.addressee],["Mavzu",q.title],
  ["Hujjat ijrochisi",q.preparer],["Ijro nazorati",(d.control||[]).join('; ')]];
 rows.forEach(([k,v,key])=>{if(v||key)h+='<dt>'+k+'</dt><dd'+(key&&(BOX['r_'+key]||[]).length?' data-k="r_'+key+'"':'')+'>'+(esc(v)||'<i>topilmadi</i>')+'</dd>'});
 h+='</dl></div><div class="card"><h2>Topshiriqlar ('+d.tasks.length+')</h2>';
 if(!d.tasks.length)h+='<p>Topshiriq topilmadi.</p>';else{h+='<table><tr class="h"><th>№</th><th>Topshiriq</th><th>Ijrochi</th><th>Muddat</th><th>Manba</th></tr>';
  d.tasks.forEach(t=>{const dl=t.deadline||{};
   const dlh=dl.type==="yo'q"?'<span class="meta">ko&#39;rsatilmagan</span>':'<b>'+esc(dl.text)+'</b><span class="tag '+esc(dl.type)+'">'+
     esc(TYPES[dl.type]||dl.type)+(dl.date&&dl.type!=='sana'?' · '+fmt(dl.date):'')+'</span>';
   h+='<tr data-k="t'+t.n+'"><td class="n">'+t.n+'</td><td>'+esc(t.text)+(t.result?'<div class="meta">Natija: '+esc(t.result)+'</div>':'')+'</td><td data-l="Ijrochi">'+
   (t.executors.map(e=>'<span class="chip">'+esc(e)+'</span>').join('')||'<i>aniqlanmadi</i>')+'</td><td class="dl" data-l="Muddat">'+dlh+
   (dl.note?'<div class="meta">'+esc(dl.note)+'</div>':'')+'</td><td class="src" data-l="Manba">'+esc(t.source)+'</td></tr>'});h+='</table>'}
 if(d.other&&d.other.length){h+='<details><summary>Topshiriq deb olinmagan qismlar ('+d.other.length+')</summary><ul class="oth">';
  d.other.forEach(o=>{h+='<li><b>'+esc(o.source)+'</b> ('+esc(o.kind)+'): '+esc(o.text)+'</li>'});h+='</ul></details>'}
 (d.warnings||[]).forEach(w=>{h+='<div class="warn">'+esc(w)+'</div>'});
 h+='</div><p class="meta">'+m.pages+' sahifa · '+(m.source==='ocr'?'skaner, OCR orqali o\'qildi'+conf:'matnli PDF')+' · '+m.seconds+' s</p></div>';
 h+='<div class="doc" id="doc">'+(d.previews||[]).map((src,i)=>'<div class="pg" data-p="'+(i+1)+'"><img src="'+src+'" alt="'+(i+1)+'-sahifa"><span class="pgn">'+(i+1)+'</span></div>').join('')+'</div></div>';
 $('out').innerHTML=h;
 $('out').querySelectorAll('[data-k]').forEach(el=>el.addEventListener('click',()=>select(el.dataset.k,el)));
 $('json').onclick=()=>save(new Blob([JSON.stringify(Object.assign({},last,{previews:undefined}),null,1)],{type:'application/json'}),base()+'.json');
 $('xlsx').onclick=async()=>{const r=await fetch('api/export',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(Object.assign({},last,{previews:undefined}))});save(await r.blob(),base()+'.xlsx')};
 $('ics').onclick=ics}
function base(){return ((last.meta.file||'natija').replace(/\.pdf$/i,''))}
function save(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click()}
function select(k,el){document.querySelectorAll('.sel').forEach(x=>x.classList.remove('sel'));el.classList.add('sel');
 document.querySelectorAll('.hl').forEach(x=>x.remove());let first=null;
 (BOX[k]||[]).forEach(b=>{const pg=document.querySelector('.pg[data-p="'+b.page+'"]');if(!pg)return;const d=document.createElement('div');d.className='hl';
  const pad=.006;d.style.left=((b.x0-pad)*100)+'%';d.style.top=((b.y0-pad)*100)+'%';d.style.width=((b.x1-b.x0+2*pad)*100)+'%';d.style.height=((b.y1-b.y0+2*pad)*100)+'%';
  pg.appendChild(d);first=first||d});
 if(first){const doc=$('doc');if(getComputedStyle(doc).position==='sticky'){doc.scrollTo({top:first.offsetTop+first.parentNode.offsetTop-doc.clientHeight/3,behavior:'smooth'})}
  else first.scrollIntoView({behavior:'smooth',block:'center'})}}
function ics(){const q=last.requisites,ev=last.tasks.filter(t=>t.deadline&&t.deadline.date&&t.deadline.type!=='boshlanish');
 if(!ev.length){alert("Aniq sanali topshiriq yo'q");return}
 const x=s=>String(s||'').replace(/\\/g,'\\\\').replace(/([,;])/g,'\\$1').replace(/\n/g,'\\n');
 const L=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//hujjat-tahlili//uz','CALSCALE:GREGORIAN'];
 ev.forEach((t,i)=>{const d=t.deadline.date.replace(/-/g,'');L.push('BEGIN:VEVENT','UID:'+Date.now()+'-'+i+'@hujjat','DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').slice(0,15)+'Z',
  'DTSTART;VALUE=DATE:'+d,'SUMMARY:'+x('Muddat: '+t.text.slice(0,80)),
  'DESCRIPTION:'+x('Ijrochi: '+t.executors.join(', ')+'\nMuddat: '+t.deadline.text+'\nHujjat: '+(q.sender||'')+', № '+(q.number||'')+', '+fmt(q.date)+'\nManba: '+t.source),'END:VEVENT')});
 L.push('END:VCALENDAR');save(new Blob([L.join('\r\n')],{type:'text/calendar'}),base()+'-muddatlar.ics')}
</script></body></html>"""
