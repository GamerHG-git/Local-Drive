import os
import uuid
import json
import time
import zipfile
import platform
import secrets
import io
import shutil as sh
from pathlib import Path
from functools import wraps
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
    session,
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

USERNAME = os.getenv("APP_USERNAME", "admin")
PASSWORD = os.getenv("APP_PASSWORD", "password123")
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drive-files")
os.makedirs(BASE_DIR, exist_ok=True)

SERVER_START_TIME = time.time()


def reload_env():
    global USERNAME, PASSWORD
    load_dotenv(override=True)
    USERNAME = os.getenv("APP_USERNAME", "admin")
    PASSWORD = os.getenv("APP_PASSWORD", "password123")


FAVORITES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "favorites.json"
)
SHARES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shares.json")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}


def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f)


def get_file_info(path):
    stat = path.stat()
    ext = path.suffix.lower() if path.is_file() else ""
    icon = get_file_icon(ext, path.is_dir())
    size = stat.st_size if path.is_file() else None
    file_path = str(path.relative_to(BASE_DIR)).replace("\\", "/")
    favorites = load_json(FAVORITES_FILE)
    return {
        "name": path.name,
        "path": file_path,
        "is_dir": path.is_dir(),
        "size": size,
        "modified": stat.st_mtime,
        "icon": icon,
        "is_favorite": file_path in favorites,
    }


def get_file_icon(ext, is_dir):
    if is_dir:
        return "folder"
    icons = {
        ".pdf": "pdf",
        ".doc": "doc",
        ".docx": "doc",
        ".xls": "xls",
        ".xlsx": "xls",
        ".ppt": "ppt",
        ".pptx": "ppt",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".gif": "image",
        ".svg": "image",
        ".webp": "image",
        ".mp4": "video",
        ".avi": "video",
        ".mov": "video",
        ".mkv": "video",
        ".mp3": "audio",
        ".wav": "audio",
        ".flac": "audio",
        ".zip": "archive",
        ".rar": "archive",
        ".7z": "archive",
        ".tar": "archive",
        ".gz": "archive",
        ".txt": "text",
        ".csv": "text",
        ".md": "text",
        ".log": "text",
        ".py": "code",
        ".js": "code",
        ".ts": "code",
        ".html": "code",
        ".css": "code",
        ".json": "code",
    }
    return icons.get(ext, "file")


def format_size(size):
    if size is None:
        return ""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_datetime(timestamp):
    from datetime import datetime

    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%b %d, %Y %I:%M %p")


app.jinja_env.filters["format_datetime"] = format_datetime

# Inline SVG icon templates
SVG_ICONS = {
    "pdf": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2 5 5h-5V4zM8 17h2v-2H8v2zm0-4h2v-2H8v2zm0-4h2V7H8v2zm4 8h4v-2h-4v2zm0-4h4v-2h-4v2z"/></svg>',
    "doc": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2 5 5h-5V4zM8 17h8v-2H8v2zm0-4h8v-2H8v2z"/></svg>',
    "xls": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2 5 5h-5V4zM9 13h6v2H9v-2zm0 4h6v2H9v-2zm0-8h2v2H9V9z"/></svg>',
    "ppt": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2 5 5h-5V4zM8 17h8v-2H8v2zm0-4h8v-2H8v2z"/></svg>',
    "image": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>',
    "video": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>',
    "audio": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>',
    "archive": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M20.54 5.23l-1.39-1.68C18.88 3.21 18.47 3 18 3H6c-.47 0-.88.21-1.16.55L3.46 5.23C3.17 5.57 3 6.02 3 6.5V19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6.5c0-.48-.17-.93-.46-1.27zM12 17.5L6.5 12H10v-2h4v2h3.5L12 17.5zM5.12 5l.81-1h12l.94 1H5.12z"/></svg>',
    "text": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2 5 5h-5V4zM8 17h8v-2H8v2zm0-4h8v-2H8v2z"/></svg>',
    "code": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/></svg>',
    "file": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2 5 5h-5V4z"/></svg>',
    "folder": '<svg class="ico ico-{size}" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>',
}


def file_icon_svg(icon_type, size="lg"):
    return SVG_ICONS.get(icon_type, SVG_ICONS["file"]).format(size=size)


app.jinja_env.globals["file_icon_svg"] = file_icon_svg
app.jinja_env.globals["USERNAME"] = USERNAME


# Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    reload_env()
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        flash("Invalid username or password", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    tab = request.args.get("tab", "home")
    subfolder = request.args.get("path", "")
    search = request.args.get("search", "")

    current_path = Path(BASE_DIR) / subfolder if subfolder else Path(BASE_DIR)
    current_path = current_path.resolve()

    if not str(current_path).startswith(str(Path(BASE_DIR).resolve())):
        flash("Access denied", "error")
        return redirect(url_for("index"))
    if not current_path.exists():
        flash("Folder not found", "error")
        return redirect(url_for("index"))

    items = []
    for entry in current_path.iterdir():
        if search.lower() in entry.name.lower():
            items.append(get_file_info(entry))
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

    breadcrumbs = []
    rel = Path(subfolder) if subfolder else Path(".")
    parts = list(rel.parts) if str(rel) != "." else []
    for i in range(len(parts)):
        breadcrumbs.append({"name": parts[i], "path": "/".join(parts[: i + 1])})

    if tab == "favorites":
        favorites = load_json(FAVORITES_FILE)
        fav_items = []
        for root, dirs, files in os.walk(BASE_DIR):
            for name in files + dirs:
                full = Path(root) / name
                fp = str(full.relative_to(BASE_DIR)).replace("\\", "/")
                if fp in favorites:
                    fav_items.append(get_file_info(full))
        items = fav_items

    return render_template(
        "index.html",
        items=items,
        current_path=subfolder,
        breadcrumbs=breadcrumbs,
        search=search,
        tab=tab,
        format_size=format_size,
    )


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    subfolder = request.form.get("path", "")
    target = Path(BASE_DIR) / subfolder if subfolder else Path(BASE_DIR)
    target = target.resolve()
    if not str(target).startswith(str(Path(BASE_DIR).resolve())):
        flash("Access denied", "error")
        return redirect(url_for("index"))
    files = request.files.getlist("files")
    for f in files:
        if f.filename:
            f.save(target / f.filename)
    flash(f"{len(files)} file(s) uploaded successfully", "success")
    return redirect(url_for("index", path=subfolder))


import mimetypes

mimetypes.init()


@app.route("/download")
@login_required
def download():
    file_path = request.args.get("path", "")
    full_path = (Path(BASE_DIR) / file_path).resolve()
    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        flash("Access denied", "error")
        return redirect(url_for("index"))
    if not full_path.exists() or full_path.is_dir():
        flash("File not found", "error")
        return redirect(url_for("index"))
    mimetype = mimetypes.guess_type(full_path.name)[0] or "application/octet-stream"
    return send_file(full_path, as_attachment=True, mimetype=mimetype)


@app.route("/download-folder")
@login_required
def download_folder():
    folder_path = request.args.get("path", "")
    full_path = (Path(BASE_DIR) / folder_path).resolve()
    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        flash("Access denied", "error")
        return redirect(url_for("index"))
    if not full_path.exists() or not full_path.is_dir():
        flash("Folder not found", "error")
        return redirect(url_for("index"))

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(full_path):
            for file in files:
                file_path = Path(root) / file
                arcname = str(file_path.relative_to(full_path))
                zf.write(file_path, arcname)
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{full_path.name}.zip",
    )


@app.route("/api/file-info")
@login_required
def file_info():
    file_path = request.args.get("path", "")
    full_path = (Path(BASE_DIR) / file_path).resolve()
    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        return jsonify({"error": "Access denied"}), 403
    if not full_path.exists():
        return jsonify({"error": "File not found"}), 404
    stat = full_path.stat()
    info = {
        "name": full_path.name,
        "size": format_size(stat.st_size),
        "modified": format_datetime(stat.st_mtime),
        "type": full_path.suffix.upper() if full_path.is_file() else "Folder",
    }
    if full_path.is_file() and full_path.suffix.lower() in [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
    ]:
        try:
            from PIL import Image

            with Image.open(full_path) as img:
                info["dimensions"] = f"{img.width} x {img.height}"
        except:
            info["dimensions"] = "N/A"
    return jsonify(info)


@app.route("/mkdir", methods=["POST"])
@login_required
def mkdir():
    subfolder = request.form.get("path", "")
    folder_name = request.form.get("folder_name", "").strip()
    if folder_name:
        target = (
            Path(BASE_DIR) / subfolder / folder_name
            if subfolder
            else Path(BASE_DIR) / folder_name
        )
        target = target.resolve()
        if str(target).startswith(str(Path(BASE_DIR).resolve())):
            target.mkdir(parents=True, exist_ok=True)
            flash(f"Folder '{folder_name}' created", "success")
    return redirect(url_for("index", path=subfolder))


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    file_path = request.form.get("path", "")
    full_path = (Path(BASE_DIR) / file_path).resolve()
    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        flash("Access denied", "error")
        return redirect(url_for("index"))
    if full_path.exists():
        if full_path.is_dir():
            sh.rmtree(full_path)
        else:
            full_path.unlink()
        flash(f"'{full_path.name}' deleted", "success")
    parent = str(Path(file_path).parent).replace("\\", "/")
    return redirect(url_for("index", path=parent if parent != "." else ""))


@app.route("/api/search")
@login_required
def api_search():
    query = request.args.get("q", "").lower()
    results = []
    for root, dirs, files in os.walk(BASE_DIR):
        for name in dirs + files:
            if query in name.lower():
                full = Path(root) / name
                results.append(get_file_info(full))
    return jsonify(results)


@app.route("/favorite", methods=["POST"])
@login_required
def toggle_favorite():
    data = request.get_json()
    file_path = data.get("path", "")
    favorites = load_json(FAVORITES_FILE)
    if file_path in favorites:
        del favorites[file_path]
        is_favorite = False
    else:
        favorites[file_path] = True
        is_favorite = True
    save_json(FAVORITES_FILE, favorites)
    return jsonify({"is_favorite": is_favorite})


@app.route("/api/server-info")
@login_required
def server_info():
    uptime = time.time() - SERVER_START_TIME
    days = int(uptime // 86400)
    hours = int((uptime % 86400) // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)

    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_used = format_size(ram.used)
        ram_total = format_size(ram.total)
        ram_percent = ram.percent
    except ImportError:
        cpu = "N/A"
        ram_used = "N/A"
        ram_total = "N/A"
        ram_percent = "N/A"

    try:
        stat = sh.disk_usage(BASE_DIR)
        disk_used = stat.used
        disk_total = stat.total
    except:
        disk_used = 0
        disk_total = 15 * 1024**4

    return jsonify(
        {
            "hostname": platform.node(),
            "os": f"{platform.system()} {platform.release()}",
            "cpu": f"{cpu}%",
            "ram_used": ram_used,
            "ram_total": ram_total,
            "ram_percent": f"{ram_percent}%",
            "disk_used": format_size(disk_used),
            "disk_total": format_size(disk_total),
            "disk_percent": round(disk_used / disk_total * 100)
            if disk_total > 0
            else 0,
            "uptime_days": days,
            "uptime_hours": hours,
            "uptime_minutes": minutes,
            "uptime_seconds": seconds,
            "start_time": SERVER_START_TIME,
        }
    )


@app.route("/api/storage")
@login_required
def storage_info():
    try:
        stat = sh.disk_usage(BASE_DIR)
        return jsonify(
            {
                "used": format_size(stat.used),
                "total": format_size(stat.total),
                "percent": round(stat.used / stat.total * 100) if stat.total > 0 else 0,
            }
        )
    except:
        return jsonify({"used": "N/A", "total": "N/A", "percent": 0})


@app.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    global USERNAME
    data = request.get_json()
    new_name = data.get("display_name", "").strip()
    if new_name:
        USERNAME = new_name
        update_env_var("APP_USERNAME", new_name)
        return jsonify({"success": True, "message": "Profile updated"})
    return jsonify({"success": False, "message": "Invalid name"}), 400


@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    global PASSWORD
    data = request.get_json()
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")
    confirm_pw = data.get("confirm_password", "")
    if old_pw != PASSWORD:
        return jsonify(
            {"success": False, "message": "Current password is incorrect"}
        ), 400
    if new_pw != confirm_pw:
        return jsonify({"success": False, "message": "New passwords do not match"}), 400
    if len(new_pw) < 4:
        return jsonify(
            {"success": False, "message": "Password must be at least 4 characters"}
        ), 400
    PASSWORD = new_pw
    update_env_var("APP_PASSWORD", new_pw)
    return jsonify({"success": True, "message": "Password changed successfully"})


def update_env_var(key, value):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(key + "="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(new_lines)


@app.route("/share", methods=["POST"])
@login_required
def share():
    data = request.get_json()
    file_path = data.get("path", "")
    full_path = (Path(BASE_DIR) / file_path).resolve()
    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        return jsonify({"error": "Access denied"}), 403
    if not full_path.exists():
        return jsonify({"error": "File not found"}), 404
    shares = load_json(SHARES_FILE)
    for token, info in shares.items():
        if info["path"] == file_path:
            base_url = request.url_root.rstrip("/")
            return jsonify({"url": f"{base_url}/s/{token}"})
    token = uuid.uuid4().hex[:16]
    shares[token] = {
        "path": file_path,
        "created": str(uuid.uuid4()),
        "is_dir": full_path.is_dir(),
    }
    save_json(SHARES_FILE, shares)
    base_url = request.url_root.rstrip("/")
    return jsonify({"url": f"{base_url}/s/{token}"})


@app.route("/s/<token>")
def share_view(token):
    shares = load_json(SHARES_FILE)
    if token not in shares:
        return "Link not found or expired", 404
    file_path = shares[token]["path"]
    full_path = (Path(BASE_DIR) / file_path).resolve()
    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        return "Access denied", 403
    if not full_path.exists():
        return "File not found", 404

    is_dir = full_path.is_dir()

    if is_dir:
        # Handle folder share
        items = []
        try:
            for item in sorted(
                full_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
            ):
                items.append(get_file_info(item))
        except Exception:
            pass

        return render_template(
            "share.html",
            token=token,
            file_name=full_path.name,
            file_size=None,
            file_icon=file_icon_svg("folder", "xl"),
            is_dir=True,
            items=items,
        )
    else:
        # Handle file share
        stat = full_path.stat()
        ext = full_path.suffix.lower()
        icon = get_file_icon(ext, False)
        return render_template(
            "share.html",
            token=token,
            file_name=full_path.name,
            file_size=format_size(stat.st_size),
            file_icon=file_icon_svg(icon, "xl"),
            is_dir=False,
            items=None,
        )


@app.route("/s/<token>/download")
def share_download(token):
    shares = load_json(SHARES_FILE)
    if token not in shares:
        return "Link not found or expired", 404
    file_path = shares[token]["path"]
    full_path = (Path(BASE_DIR) / file_path).resolve()
    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        return "Access denied", 403
    if not full_path.exists():
        return "File not found", 404

    is_dir = full_path.is_dir()

    if is_dir:
        # Download folder as zip
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path_item = Path(root) / file
                    arcname = str(file_path_item.relative_to(full_path))
                    zf.write(file_path_item, arcname)
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{full_path.name}.zip",
        )
    else:
        # Download single file
        mimetype = mimetypes.guess_type(full_path.name)[0] or "application/octet-stream"
        return send_file(full_path, as_attachment=True, mimetype=mimetype)


@app.route("/rename", methods=["POST"])
@login_required
def rename():
    old_path = request.form.get("old_path", "")
    new_name = request.form.get("new_name", "").strip()

    if not new_name:
        flash("Name cannot be empty", "error")
        return redirect(url_for("index"))

    full_old_path = (Path(BASE_DIR) / old_path).resolve()
    if not str(full_old_path).startswith(str(Path(BASE_DIR).resolve())):
        flash("Access denied", "error")
        return redirect(url_for("index"))

    if not full_old_path.exists():
        flash("File not found", "error")
        return redirect(url_for("index"))

    # Create new path with same parent directory
    parent = full_old_path.parent
    new_full_path = parent / new_name

    # Check if new name already exists
    if new_full_path.exists():
        flash(f"'{new_name}' already exists", "error")
        parent_path = str(Path(old_path).parent).replace("\\", "/")
        return redirect(
            url_for("index", path=parent_path if parent_path != "." else "")
        )

    try:
        full_old_path.rename(new_full_path)
        flash(f"Renamed to '{new_name}'", "success")
    except Exception as e:
        flash(f"Error renaming: {str(e)}", "error")

    parent_path = str(Path(old_path).parent).replace("\\", "/")
    return redirect(url_for("index", path=parent_path if parent_path != "." else ""))


@app.route("/copy", methods=["POST"])
@login_required
def copy_file():
    data = request.get_json()
    file_path = data.get("path", "")
    full_path = (Path(BASE_DIR) / file_path).resolve()

    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        return jsonify({"error": "Access denied"}), 403
    if not full_path.exists():
        return jsonify({"error": "File not found"}), 404

    # Store in session for paste operation
    session["clipboard"] = {"path": file_path, "operation": "copy"}
    return jsonify({"success": True, "message": "Copied to clipboard"})


@app.route("/cut", methods=["POST"])
@login_required
def cut_file():
    data = request.get_json()
    file_path = data.get("path", "")
    full_path = (Path(BASE_DIR) / file_path).resolve()

    if not str(full_path).startswith(str(Path(BASE_DIR).resolve())):
        return jsonify({"error": "Access denied"}), 403
    if not full_path.exists():
        return jsonify({"error": "File not found"}), 404

    # Store in session for paste operation
    session["clipboard"] = {"path": file_path, "operation": "cut"}
    return jsonify({"success": True, "message": "Cut to clipboard"})


@app.route("/paste", methods=["POST"])
@login_required
def paste_file():
    data = request.get_json()
    target_folder = data.get("target_path", "")

    if "clipboard" not in session:
        return jsonify({"error": "Clipboard is empty"}), 400

    clipboard = session["clipboard"]
    source_path = clipboard.get("path", "")
    operation = clipboard.get("operation", "copy")

    source_full = (Path(BASE_DIR) / source_path).resolve()
    target_full = (
        (Path(BASE_DIR) / target_folder).resolve() if target_folder else Path(BASE_DIR)
    )

    if not str(source_full).startswith(str(Path(BASE_DIR).resolve())) or not str(
        target_full
    ).startswith(str(Path(BASE_DIR).resolve())):
        return jsonify({"error": "Access denied"}), 403

    if not source_full.exists() or not target_full.exists() or not target_full.is_dir():
        return jsonify({"error": "Invalid source or target"}), 404

    try:
        new_path = target_full / source_full.name

        # If file/folder already exists and it's a copy operation, rename with (1), (2), etc.
        if new_path.exists() and operation == "copy":
            name_parts = source_full.name.rsplit(".", 1)
            if len(name_parts) == 2:
                base_name, ext = name_parts
                counter = 1
                while new_path.exists():
                    new_name = f"{base_name} ({counter}).{ext}"
                    new_path = target_full / new_name
                    counter += 1
            else:
                base_name = source_full.name
                counter = 1
                while new_path.exists():
                    new_name = f"{base_name} ({counter})"
                    new_path = target_full / new_name
                    counter += 1

        if operation == "cut":
            source_full.rename(new_path)
            session.pop("clipboard", None)
            return jsonify({"success": True, "message": f"Moved '{source_full.name}'"})
        else:  # copy
            if source_full.is_dir():
                sh.copytree(source_full, new_path)
            else:
                sh.copy2(source_full, new_path)
            return jsonify({"success": True, "message": f"Copied '{source_full.name}'"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/check-clipboard", methods=["GET"])
@login_required
def check_clipboard():
    if "clipboard" in session:
        return jsonify(
            {
                "has_clipboard": True,
                "operation": session["clipboard"].get("operation", "copy"),
            }
        )
    return jsonify({"has_clipboard": False})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Local Drive on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
