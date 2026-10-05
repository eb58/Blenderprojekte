"""Lokales Museum Studio. Start mit Blenders mitgeliefertem Python."""
import argparse
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
DEFAULTS = dict(RENDER_PRESET="test", BODEN="marmor", RESOLUTION_X=1280,
                RESOLUTION_Y=800, FPS=24, DURATION=5, SCULPTURE_SCALE=3.55,
                THICKNESS=0.06, ORBIT_DEGREES=360,
                OUTPUT_DIR=str(ROOT / "Render" / "kusner_p7_granit_museum"))
TOKEN = secrets.token_urlsafe(24)
LOCK = threading.Lock()
STATE = dict(process=None, settings=DEFAULTS.copy(), kind="", log=None,
             started=0, preview=None, video=None)


def find_ffmpeg():
    """Find FFmpeg via PATH or its standard per-user WinGet location."""
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        packages = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        candidates = packages.glob("Gyan.FFmpeg_*/*/bin/ffmpeg.exe")
        existing = [path for path in candidates if path.is_file()]
        if existing:
            return str(max(existing, key=lambda path: path.stat().st_mtime_ns))
    return None


def validate(data):
    result = DEFAULTS.copy()
    for key in result:
        if key in data:
            result[key] = data[key]
    if result["RENDER_PRESET"] not in ("test", "final_fast", "animation", "quality"):
        raise ValueError("Unbekannte Renderqualität.")
    if result["BODEN"] not in ("marmor", "parkett"):
        raise ValueError("Unbekannter Boden.")
    limits = dict(RESOLUTION_X=(64, 8192), RESOLUTION_Y=(64, 8192), FPS=(1, 120),
                  DURATION=(0.1, 3600), SCULPTURE_SCALE=(0.1, 10),
                  THICKNESS=(0.001, 1), ORBIT_DEGREES=(-3600, 3600))
    for key, (low, high) in limits.items():
        value = float(str(result[key]).replace(",", "."))
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{key}: Wert muss zwischen {low} und {high} liegen.")
        if key in ("RESOLUTION_X", "RESOLUTION_Y", "FPS"):
            if not value.is_integer():
                raise ValueError(f"{key}: ganze Zahl erforderlich.")
            value = int(value)
        result[key] = value
    if result["FPS"] * result["DURATION"] < 2:
        raise ValueError("Mindestens zwei Frames erforderlich.")
    path = Path(result["OUTPUT_DIR"])
    if not path.is_absolute():
        raise ValueError("Bitte einen absoluten Ausgabeordner angeben.")
    result["OUTPUT_DIR"] = str(path.resolve())
    return result


def start_job(kind, data):
    with LOCK:
        process = STATE["process"]
        if process and process.poll() is None:
            raise ValueError("Ein Auftrag läuft bereits.")
        settings = validate(data)
        folder = Path(settings["OUTPUT_DIR"])
        folder.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        if kind in ("still", "animation"):
            settings.update(MAKE_VIDEO=kind == "animation", RESUME_RENDER=True)
            config = folder / ("settings.json" if kind == "animation" else "test-settings.json")
            if kind == "animation" and any((folder / "frames").glob("frame_*.png")):
                if not config.exists() or json.loads(config.read_text(encoding="utf-8-sig")) != settings:
                    raise ValueError("Vorhandene Frames gehören zu anderen Einstellungen. Bitte einen neuen Ausgabeordner wählen.")
            blender = str(BLENDER) if BLENDER.exists() else shutil.which("blender")
            if not blender:
                raise ValueError("Blender wurde nicht gefunden.")
            config.write_text(json.dumps(settings, indent=2), encoding="utf-8")
            env["MUSEUM_CONFIG"] = str(config)
            args = [blender, "--background", "--factory-startup", "--python-exit-code", "1",
                    "--python", str(ROOT / "museum_komplett.py")]
            args += ["--render-anim"] if kind == "animation" else ["--render-frame", "1"]
            STATE["preview"] = None
            STATE["video"] = None
        elif kind == "video":
            config = folder / "settings.json"
            if not config.exists():
                raise ValueError("Bitte zuerst eine Animation rendern.")
            settings = validate(json.loads(config.read_text(encoding="utf-8-sig")))
            count = max(2, round(settings["FPS"] * settings["DURATION"]))
            for number in range(1, count + 1):
                if not (folder / "frames" / f"frame_{number:04d}.png").exists():
                    raise ValueError(f"Frame {number} fehlt. Animation erst fertig rendern.")
            ffmpeg = find_ffmpeg()
            if not ffmpeg:
                raise ValueError("FFmpeg fehlt im PATH. PNG-Frames können bereits gerendert werden.")
            if settings["RESOLUTION_X"] % 2 or settings["RESOLUTION_Y"] % 2:
                raise ValueError("Für MP4 bitte eine gerade Bildbreite und -höhe verwenden.")
            video = folder / f"museum_{time.time_ns()}.mp4"
            args = [ffmpeg, "-n", "-framerate", str(settings["FPS"]), "-start_number", "1",
                    "-i", str(folder / "frames" / "frame_%04d.png"), "-frames:v", str(count),
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(video)]
            STATE["video"] = video
        else:
            raise ValueError("Unbekannter Auftrag.")
        log_folder = folder / "logs"
        log_folder.mkdir(parents=True, exist_ok=True)
        log_path = log_folder / f"{kind}_{time.time_ns()}.log"
        with log_path.open("wb") as log:
            process = subprocess.Popen(args, cwd=folder, env=env, stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        STATE.update(process=process, settings=settings, kind=kind, log=log_path, started=time.time())


def status():
    with LOCK:
        settings = STATE["settings"]
        folder = Path(settings["OUTPUT_DIR"])
        frames = sorted((folder / "frames").glob("frame_*.png"))
        # Blender appends the frame number when invoked with --render-frame,
        # even when the configured output path already ends in ".png".
        # Select the newest matching render instead of showing a stale image.
        stills = list(folder.glob("kusner_p7_museum_test*.png"))
        still = max(stills, key=lambda path: path.stat().st_mtime_ns) if stills else None
        preview = still if STATE["kind"] != "animation" and still else (frames[-1] if frames else None)
        STATE["preview"] = preview
        process = STATE["process"]
        code = process.poll() if process else None
        running = bool(process and code is None)
        log = STATE["log"]
        tail = ""
        if log and log.exists():
            with log.open("rb") as source:
                source.seek(max(0, log.stat().st_size - 14000))
                tail = source.read().decode("utf-8", errors="replace")
        total = max(2, round(settings["FPS"] * settings["DURATION"]))
        return dict(running=running, code=code, kind=STATE["kind"], frames=len(frames), total=total,
                    preview=preview.stat().st_mtime_ns if preview else None,
                    video=bool(STATE["video"] and STATE["video"].exists() and code == 0),
                    log=tail, elapsed=int(time.time()-STATE["started"]) if process else 0,
                    ffmpeg=bool(find_ffmpeg()))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, code, body, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = self.path.split("?")[0]
        if route == "/":
            html = (ROOT / "museum_studio.html").read_text(encoding="utf-8")
            html = html.replace("__BOOT__", json.dumps(dict(token=TOKEN, defaults=DEFAULTS)))
            self.send(200, html.encode(), "text/html; charset=utf-8")
        elif route == "/api/status":
            self.send(200, json.dumps(status()).encode())
        elif route in ("/preview", "/video"):
            path = STATE["preview" if route == "/preview" else "video"]
            if path and path.exists():
                self.send(200, path.read_bytes(), "image/png" if route == "/preview" else "video/mp4")
            else:
                self.send(404, b"Not found", "text/plain")
        else:
            self.send(404, b"{}")

    def do_POST(self):
        if self.headers.get("X-Museum-Token") != TOKEN:
            message = {"error": "Museum Studio wurde neu gestartet. Bitte die Seite neu laden."}
            self.send(403, json.dumps(message).encode())
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16000:
                raise ValueError("Ungültige Anfrage.")
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/start":
                start_job(data["kind"], data["settings"])
            elif self.path == "/api/stop":
                with LOCK:
                    process = STATE["process"]
                    if process and process.poll() is None:
                        process.terminate()
            else:
                raise ValueError("Unbekannte Aktion.")
            self.send(200, b'{"ok":true}')
        except (ValueError, KeyError, OSError) as error:
            self.send(400, json.dumps(dict(error=str(error))).encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    options = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", options.port), Handler)
    print(f"Museum Studio: http://127.0.0.1:{server.server_port}", flush=True)
    server.serve_forever()
