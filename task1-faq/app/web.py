"""Veb-sahifalar: fuqaro uchun suhbat ko'rinishidagi sahifa va admin sahifasi (oddiy HTML, tashqi kutubxonasiz)."""

PAGE = r"""<!doctype html>
<html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Davlat xizmatlari bo'yicha savol-javob</title>
<style>
:root{--bg:#eef2f6;--card:#fff;--ink:#17202c;--mut:#5f6b7a;--line:#dfe5ec;--acc:#1f6feb;--me:#dcebff}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.app{max-width:760px;height:100%;margin:0 auto;display:flex;flex-direction:column;background:var(--card)}
header{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px}
header h1{font-size:17px;margin:0;flex:1}header small{display:block;color:var(--mut);font-weight:400;font-size:13px}
.topics{border:1px solid var(--line);background:#fff;border-radius:8px;padding:7px 12px;font:inherit;font-size:14px;cursor:pointer}
#chat{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:88%;padding:10px 14px;border-radius:14px;white-space:pre-wrap;word-wrap:break-word}
.me{align-self:flex-end;background:var(--me);border-bottom-right-radius:4px}
.bot{align-self:flex-start;background:#f4f6f9;border-bottom-left-radius:4px}
.bot b{display:block;margin-bottom:4px}
.row{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{border:1px solid #c9d6e6;background:#fff;color:#174ea6;border-radius:16px;padding:5px 11px;font:inherit;font-size:13.5px;cursor:pointer;text-align:left}
.chip:hover{background:#eef4ff}.fb{border-color:var(--line);color:var(--mut)}
.mut{color:var(--mut);font-size:13px;margin-top:6px}
form{display:flex;gap:8px;padding:12px;border-top:1px solid var(--line)}
input{flex:1;padding:12px 14px;border:1px solid #c9d1dc;border-radius:22px;font:inherit;outline:none}
input:focus{border-color:var(--acc)}
.btn{width:46px;height:46px;border-radius:50%;border:0;background:var(--acc);color:#fff;cursor:pointer;flex:none;display:grid;place-items:center}
.mic{background:#eef1f5;color:var(--ink)}.mic.rec{background:#d93025;color:#fff;animation:p 1s infinite}
@keyframes p{50%{opacity:.6}}
.typing{color:var(--mut);font-size:14px;align-self:flex-start}
</style></head><body><div class="app">
<header><h1>Davlat xizmatlari bo'yicha savol-javob<small>Savolingizni o'z so'zingiz bilan yozing yoki ovozli yuboring</small></h1>
<button class="topics" id="topics">Mavzular</button></header>
<div id="chat"></div>
<form id="f"><input id="q" placeholder="Masalan: ID-karta olish uchun nima kerak?" autocomplete="off">
<button type="button" class="btn mic" id="mic" title="Ovozli savol"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg></button><button class="btn" title="Yuborish"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 20l18-8L3 4v6l12 2-12 2z"/></svg></button></form>
</div>
<script>
const chat=document.getElementById('chat'),q=document.getElementById('q');
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function add(cls,html){const d=document.createElement('div');d.className='msg '+cls;d.innerHTML=html;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;return d}
function chips(items){return items&&items.length?'<div class="row">'+items.map(a=>'<button class="chip" data-a="'+a.answer_id+'">'+esc(a.question)+'</button>').join('')+'</div>':''}
function typing(on){let t=document.getElementById('typing');if(on&&!t){t=document.createElement('div');t.id='typing';t.className='typing';t.textContent='Javob qidirilmoqda...';chat.appendChild(t);chat.scrollTop=chat.scrollHeight}if(!on&&t)t.remove()}
async function api(path,opt){const r=await fetch(path,opt);if(!r.ok)throw new Error('xato '+r.status);return r.json()}
async function ask(text,voice){add('me',(voice?'<span class="mut">ovozli: </span>':'')+esc(text));typing(true);
 try{const d=await api('ask',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({question:text,channel:'web',voice:!!voice})});typing(false);show(d)}
 catch(e){typing(false);add('bot','Hozir javob bera olmayapman, birozdan keyin qayta urinib ko\'ring.')}}
function show(d){
 if(d.status==='answered'){add('bot','<b>'+esc(d.question)+'</b>'+esc(d.answer)+
   '<div class="row"><button class="chip fb" data-f="'+d.log_id+':1">Foydali</button><button class="chip fb" data-f="'+d.log_id+':0">Bu emas</button></div>'+
   (d.alternatives.length?'<div class="mut">O\'xshash savollar:</div>'+chips(d.alternatives):''))}
 else{add('bot',esc(d.message)+chips(d.alternatives)+(d.status==='not_found'?'<div class="row"><button class="chip" data-t="1">Mavzular ro\'yxati</button></div>':''))}}
async function answer(id){typing(true);const a=await api('answers/'+id);typing(false);add('bot','<b>'+esc(a.question)+'</b>'+esc(a.answer))}
async function topics(){const c=await api('categories');add('bot','Qaysi mavzu kerak?'+'<div class="row">'+c.map(x=>'<button class="chip" data-c="'+x.id+':0">'+esc(x.name)+' ('+x.count+')</button>').join('')+'</div>')}
async function topic(id,page){const c=await api('categories/'+id+'?page='+page);add('bot','<b>'+esc(c.name)+'</b>'+
 chips(c.items)+(c.page+1<c.pages?'<div class="row"><button class="chip" data-c="'+id+':'+(c.page+1)+'">Yana ko\'rsatish</button></div>':''))}
chat.addEventListener('click',async e=>{const b=e.target.closest('button');if(!b)return;
 if(b.dataset.a)answer(b.dataset.a);
 if(b.dataset.t)topics();
 if(b.dataset.c){const[i,p]=b.dataset.c.split(':');topic(i,+p)}
 if(b.dataset.f){const[id,v]=b.dataset.f.split(':');b.parentNode.querySelectorAll('button').forEach(x=>x.disabled=true);
   const r=await api('feedback',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({log_id:+id,useful:v==='1'})});
   if(v==='1')b.textContent='Rahmat!';else add('bot',r.alternatives.length?'Kechirasiz. Balki shulardan biri kerakdir:'+chips(r.alternatives):'Kechirasiz. Savolni boshqacharoq yozib ko\'ring.')}});
document.getElementById('topics').onclick=topics;
document.getElementById('f').onsubmit=e=>{e.preventDefault();const t=q.value.trim();if(t){q.value='';ask(t)}};
let rec=null,parts=[];const mic=document.getElementById('mic');
mic.onclick=async()=>{if(rec&&rec.state==='recording'){rec.stop();return}
 try{const st=await navigator.mediaDevices.getUserMedia({audio:true});rec=new MediaRecorder(st);parts=[];
  rec.ondataavailable=e=>parts.push(e.data);rec.onstop=async()=>{st.getTracks().forEach(t=>t.stop());mic.classList.remove('rec');
   const fd=new FormData();fd.append('file',new Blob(parts,{type:rec.mimeType}),'voice.webm');typing(true);
   try{const r=await api('stt',{method:'POST',body:fd});typing(false);if(r.text)ask(r.text,true);else add('bot','Ovozni tushuna olmadim. Yana bir bor aniqroq aytib ko\'ring yoki yozib yuboring.')}
   catch(e){typing(false);add('bot','Ovozni tanib bo\'lmadi, yozib yuboring.')}};
  rec.start();mic.classList.add('rec');setTimeout(()=>{if(rec.state==='recording')rec.stop()},15000)}
 catch(e){add('bot','Mikrofonga ruxsat berilmadi. Savolni yozib yuboring.')}};
add('bot','Assalomu alaykum! Davlat xizmatlari bo\'yicha savolingizni yozing yoki mikrofon tugmasini bosib ayting. Nima so\'rashni bilmasangiz, mavzular ro\'yxatidan tanlang.');
</script></body></html>"""


ADMIN_PAGE = r"""<!doctype html>
<html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Savol-javob: admin</title>
<style>
:root{--bg:#f5f7fa;--card:#fff;--ink:#1c2330;--mut:#5d6778;--line:#e3e8ef;--acc:#1f6feb}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14.5px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:26px 18px 60px}h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:18px}
.c{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}.c b{font-size:22px;display:block}.c span{color:var(--mut);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:18px}
h2{font-size:16px;margin:0 0 10px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:7px 6px;border-top:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:600;font-size:12.5px;border-top:0}.st{font-size:12px;border-radius:5px;padding:1px 6px;background:#eef1f5}
.answered{background:#e6f4ea;color:#1a7f37}.unsure{background:#fff4d6;color:#9a6700}.not_found{background:#fde8e7;color:#b42318}
select,button,input[type=file]{font:inherit}button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer}
.mut{color:var(--mut)}
</style></head><body><main>
<h1>Savol-javob: admin</h1><p class="sub">Bot va veb-sahifaga kelgan savollar. Javobsiz qolganlari bazaga qaysi javoblarni qo'shish kerakligini ko'rsatadi.
 Davr: <select id="days"><option value="1">1 kun</option><option value="7" selected>7 kun</option><option value="30">30 kun</option></select></p>
<div class="cards" id="cards"></div>
<div class="card"><h2>Bot javob topa olmagan savollar</h2><p class="mut">"Topilmadi" deyilgan yoki foydalanuvchi "Bu emas" degan savollar. Ko'p takrorlanganini bazaga qo'shish kerak.</p><table id="gaps"></table></div>
<div class="card"><h2>Eng ko'p berilgan javoblar</h2><table id="top"></table></div>
<div class="card"><h2>Oxirgi savollar</h2><table id="recent"></table></div>
<div class="card"><h2>Bazani yangilash</h2>
<p class="mut">Excel: "answers" va "questions" varaqlari yoki "savol | javob" ustunlari bo'lgan bitta varaq. Yuklangach, indeks qayta quriladi (CPU da 10-15 daqiqa), bot shu vaqtda eski indeks bilan ishlayveradi.</p>
<form id="up"><input type="file" name="file" accept=".xlsx,.xls,.csv" required> <label><input type="checkbox" name="replace" value="true"> eski bazani to'liq almashtirish</label> <button>Yuklash</button></form>
<p id="job" class="mut"></p></div>
<script>
const $=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pct=(a,b)=>b?Math.round(100*a/b)+'%':'-';
const ST={answered:'javob berildi',unsure:'variantlar',not_found:'topilmadi'};
async function load(){const r=await fetch('admin/data?days='+$('days').value);if(!r.ok){document.body.innerHTML='<p style="margin:40px">Ruxsat yo\'q</p>';return}
 const d=await r.json(),s=d.summary;
 $('cards').innerHTML=[[s.total,'savol'],[s.users,'foydalanuvchi'],[pct(s.answered,s.total),'darhol javob'],[pct(s.unsure,s.total),'variant ko\'rsatildi'],
  [pct(s.not_found,s.total),'topilmadi'],[s.likes+' / '+s.dislikes,'foydali / foydasiz'],[s.voice,'ovozli savol'],[s.median_ms+' ms','o\'rtacha javob vaqti']]
  .map(([a,b])=>'<div class="c"><b>'+a+'</b><span>'+b+'</span></div>').join('');
 $('gaps').innerHTML='<tr><th>Savol</th><th>Necha marta</th><th>Oxirgi marta</th></tr>'+(d.gaps.map(g=>'<tr><td>'+esc(g.query)+'</td><td>'+g.n+'</td><td>'+esc(g.last.slice(0,16))+'</td></tr>').join('')||'<tr><td colspan=3 class="mut">Hozircha yo\'q</td></tr>');
 $('top').innerHTML='<tr><th>Javob</th><th>Necha marta</th></tr>'+(d.top.map(t=>'<tr><td>'+t.answer_id+': '+esc(t.question)+'</td><td>'+t.n+'</td></tr>').join('')||'<tr><td colspan=2 class="mut">Hozircha yo\'q</td></tr>');
 $('recent').innerHTML='<tr><th>Vaqt</th><th>Kanal</th><th>Savol</th><th>Natija</th><th>Baho</th><th>ms</th></tr>'+d.recent.map(r=>'<tr><td>'+esc(r.ts.slice(5,16))+'</td><td>'+esc(r.channel)+(r.voice?' &#127908;':'')+'</td><td>'+esc(r.query)+'</td><td><span class="st '+r.status+'">'+(ST[r.status]||r.status)+'</span></td><td>'+(r.feedback===1?'&#128077;':r.feedback===-1?'&#128078;':'')+'</td><td>'+r.latency_ms+'</td></tr>').join('');
 const j=d.job;$('job').textContent=j.state==='running'?'Yangilanmoqda: '+j.step:j.state==='done'?'Oxirgi yangilash muvaffaqiyatli: '+j.items+' ta matn indekslandi':j.state==='error'?'Xato: '+j.error:''}
$('days').onchange=load;load();setInterval(load,30000);
$('up').onsubmit=async e=>{e.preventDefault();const r=await fetch('admin/upload',{method:'POST',body:new FormData(e.target)});const d=await r.json();
 $('job').textContent=r.ok?'Qabul qilindi: '+d.answers+' javob, '+d.questions+' savol. Indeks qurilmoqda...':'Xato: '+(d.detail||r.status);setTimeout(load,2000)};
</script></main></body></html>"""
