const $=id=>document.getElementById(id);
let currentUrl="", selected="best", formats=[], downloading=false;

function showError(s){$("error").textContent=s||""}
function prettyDuration(sec){if(!sec)return "";sec=Number(sec);let h=Math.floor(sec/3600),m=Math.floor(sec%3600/60),s=sec%60;return h?`${h}h ${m}m ${s}s`:`${m}m ${s}s`}
function mb(n){if(!n)return "—";return `${(Number(n)/1048576).toFixed(1)} MB`}
function etaText(seconds){if(seconds===null||seconds===undefined||isNaN(seconds))return "—";let x=Number(seconds)/60;return `${x.toFixed(1)} min`}

$("inspect").onclick=async()=>{
 currentUrl=$("url").value.trim();
 if(!currentUrl){showError("Paste a YouTube URL first.");return}
 showError("");$("inspect").disabled=true;$("inspect").textContent="Inspecting…";
 try{
  let r=await fetch("/api/info",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:currentUrl})});
  let d=await r.json();if(!r.ok)throw Error(d.error);
  $("details").classList.remove("hidden");$("thumb").src=d.thumbnail||"";$("dlThumb").src=d.thumbnail||"";$("title").textContent=d.title;$("dlName").textContent=d.title;$("duration").textContent=prettyDuration(d.duration);
  formats=d.formats||[];renderFormats();$("downloadPanel").classList.add("hidden");
 }catch(e){showError(e.message||"Could not inspect this link.")}finally{$("inspect").disabled=false;$("inspect").textContent="⌕  Inspect"}
};

function renderFormats(){
 let box=$("formats");box.innerHTML="";
 let best=document.createElement("div");best.className="fmt selected";
 best.innerHTML="<strong>Best available <small style='display:inline;color:#75a4ff'> HD</small></strong><small>Highest quality automatically</small>";
 best.onclick=()=>select("best",best);box.appendChild(best);
 formats.forEach(f=>{
  let d=document.createElement("div");d.className="fmt";
  d.innerHTML=`<strong>${f.label}</strong><small>${f.ext.toUpperCase()} · ${f.size?mb(f.size):"Size calculated during download"}</small>`;
  d.onclick=()=>select(f.id,d);box.appendChild(d);
 });
}
function select(id,el){selected=id;document.querySelectorAll(".fmt").forEach(x=>x.classList.remove("selected"));el.classList.add("selected");startDownload()}
$("best").onclick=()=>{let x=document.querySelector(".fmt");if(x)select("best",x)}

async function startDownload(){
 if(!currentUrl||downloading)return;downloading=true;
 $("downloadPanel").classList.remove("hidden");$("save").classList.add("hidden");$("state").textContent="Starting…";
 try{
  let r=await fetch("/api/download",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:currentUrl,format:selected})});
  let d=await r.json();if(!r.ok)throw Error(d.error);poll(d.job_id);
 }catch(e){showError(e.message);$("state").textContent="Failed";downloading=false}
}
async function poll(id){
 try{
  let d=await (await fetch("/api/progress/"+id)).json();
  $("pct").textContent=(d.percent||0)+"%";$("bar").style.width=(d.percent||0)+"%";
  $("rom").textContent=d.total?`${mb(d.downloaded)} / ${mb(d.total)}`:"Calculating…";
  $("speed").textContent=d.speed||"—";
  $("eta").textContent=d.eta&&d.eta!=="—"?etaText(parseFloat(d.eta)):"—";
  if(d.status==="done"){
    $("state").textContent="Download complete";let a=$("save");a.href="/api/file/"+id;a.classList.remove("hidden");downloading=false;return
  }
  if(d.status==="error"){showError(d.error||"Download failed.");$("state").textContent="Failed";downloading=false;return}
  $("state").textContent=d.status==="processing"?"Finalizing…":"Downloading…";setTimeout(()=>poll(id),650)
 }catch(e){showError("Lost connection to local server.");downloading=false}
}
document.querySelectorAll(".nav").forEach(btn=>btn.onclick=()=>{
 document.querySelectorAll(".nav").forEach(x=>x.classList.remove("active"));btn.classList.add("active");
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("activeTab"));$(btn.dataset.tab).classList.add("activeTab")
});
$("url").addEventListener("keydown",e=>{if(e.key==="Enter")$("inspect").click()});
