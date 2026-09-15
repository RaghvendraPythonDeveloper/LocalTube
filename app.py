import os, uuid, threading, time, re
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

BASE = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# YouTube changes its player clients frequently. These settings avoid the
# problematic tv_downgraded client seen in recent yt-dlp/YouTube errors.
YOUTUBE_EXTRACTOR_ARGS = {
    "youtube": {
        "player_client": ["default", "web_embedded"]
    }
}

app = Flask(__name__)

jobs = {}

def human_bytes(n):
    if not n: return "—"
    n=float(n)
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.1f} {unit}"
        n/=1024
    return f"{n:.1f} PB"

def hook_factory(job_id):
    def hook(d):
        j=jobs.get(job_id)
        if not j: return
        status=d.get("status")
        if status=="downloading":
            total=d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done=d.get("downloaded_bytes") or 0
            speed=d.get("speed") or 0
            eta=d.get("eta")
            j.update({
                "status":"downloading",
                "downloaded":done,
                "total":total,
                "percent":round(done*100/total,1) if total else 0,
                "speed":human_bytes(speed)+"/s" if speed else "—",
                "eta":eta if eta is not None else None,
            })
        elif status=="finished":
            j.update({"status":"processing","percent":100,"speed":"—","eta":"—"})
    return hook

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/info", methods=["POST"])
def info():
    url=request.json.get("url","").strip()
    if not re.match(r"^https?://", url):
        return jsonify({"error":"Please paste a valid YouTube URL."}),400
    opts={"quiet":True,"no_warnings":True,"skip_download":True,"extractor_args":YOUTUBE_EXTRACTOR_ARGS}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info(url, download=False)
        formats=[]
        for f in info.get("formats",[]):
            if f.get("vcodec")=="none" and f.get("acodec")=="none": continue
            height=f.get("height")
            vcodec=f.get("vcodec")
            acodec=f.get("acodec")
            if not height and vcodec=="none": 
                # audio-only
                abr=f.get("abr")
                if abr:
                    formats.append({"id":f["format_id"],"label":f"Audio • {round(abr)} kbps","type":"audio",
                                    "ext":f.get("ext","m4a"),"size":f.get("filesize") or f.get("filesize_approx")})
                continue
            if height and vcodec!="none":
                fps=f.get("fps")
                label=f"{height}p"+(f" • {round(fps)} fps" if fps else "")
                if acodec=="none": label+=" • video"
                else: label+=" • video + audio"
                formats.append({"id":f["format_id"],"label":label,"type":"video",
                                "ext":f.get("ext","mp4"),"size":f.get("filesize") or f.get("filesize_approx")})
        # Keep useful unique resolutions, prefer combined formats, and audio.
        seen=set(); clean=[]
        for x in sorted(formats, key=lambda z:(z["type"]!="video", -(int(re.search(r'\d+',z["label"]).group()) if re.search(r'\d+',z["label"]) else 0))):
            key=(x["type"],x["label"].split(" • ")[0])
            if key not in seen:
                seen.add(key); clean.append(x)
        return jsonify({"title":info.get("title","YouTube video"),"thumbnail":info.get("thumbnail"),
                        "duration":info.get("duration"),"formats":clean})
    except Exception as e:
        return jsonify({"error":str(e).split("\n")[0]}),500

@app.route("/api/download", methods=["POST"])
def download():
    data=request.json
    url=data.get("url","").strip()
    fmt=data.get("format","best")
    job_id=str(uuid.uuid4())
    jobs[job_id]={"status":"starting","percent":0,"speed":"—","eta":"—","downloaded":0,"total":0}
    def worker():
        try:
            # Prefer MP4-compatible combined format when possible. For selected formats,
            # yt-dlp may merge video+audio with ffmpeg if necessary.
            if fmt=="audio":
                format_spec="bestaudio/best"
                opts_extra={"postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]}
            elif fmt=="best":
                format_spec="bestvideo*+bestaudio/best"
                opts_extra={}
            else:
                # Format id supplied by the info endpoint.
                format_spec=f"{fmt}+bestaudio/{fmt}"
                opts_extra={}
            out=os.path.join(DOWNLOAD_DIR, "%(title).200s [%(id)s].%(ext)s")
            opts={"quiet":True,"no_warnings":True,"format":format_spec,"outtmpl":out,
                  "merge_output_format":"mp4","progress_hooks":[hook_factory(job_id)],"extractor_args":YOUTUBE_EXTRACTOR_ARGS,**opts_extra}
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            matches=[os.path.join(DOWNLOAD_DIR,x) for x in os.listdir(DOWNLOAD_DIR)
                     if os.path.isfile(os.path.join(DOWNLOAD_DIR,x))]
            latest=max(matches,key=os.path.getmtime) if matches else None
            jobs[job_id].update({"status":"done","percent":100,"file":latest})
        except Exception as e:
            jobs[job_id].update({"status":"error","error":str(e).split("\n")[0]})
    threading.Thread(target=worker,daemon=True).start()
    return jsonify({"job_id":job_id})

@app.route("/api/progress/<job_id>")
def progress(job_id):
    return jsonify(jobs.get(job_id,{"status":"error","error":"Job not found"}))

@app.route("/api/file/<job_id>")
def get_file(job_id):
    j=jobs.get(job_id)
    if not j or j.get("status")!="done" or not j.get("file") or not os.path.exists(j["file"]):
        return "File not ready",404
    return send_file(j["file"], as_attachment=True)

if __name__=="__main__":
    print("\n  YouTube Local Downloader")
    print("  Open: http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1",port=5000,debug=False)
