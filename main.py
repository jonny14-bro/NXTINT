# main.py (NEXINT v1 – ENTRY POINT)

from flask import Flask, request, jsonify
import tempfile
import os

import shared  # your offline framework

app = Flask(__name__)


import numpy as np
import torch

def to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [to_json_safe(v) for v in obj]

    if isinstance(obj, tuple):
        return [to_json_safe(v) for v in obj]

    if isinstance(obj, set):
        return list(obj)

    if isinstance(obj, np.ndarray):
        return {
            "__type__": "ndarray",
            "shape": obj.shape,
            "dtype": str(obj.dtype)
        }

    if isinstance(obj, torch.Tensor):
        return {
            "__type__": "tensor",
            "shape": list(obj.shape),
            "dtype": str(obj.dtype)
        }

    if hasattr(obj, "__dict__"):
        return to_json_safe(obj.__dict__)

    return str(obj)



# --------------------------------------------------
# SYSTEM STATUS (BOOT CHECK)
# --------------------------------------------------
@app.route("/api/system/ping", methods=["GET"])
def system_ping():
    return jsonify({
        "status": "OK",
        "mode": "OFFLINE",
        "engine": "NEXINT"
    })




# --------------------------------------------------
# IMAGE SCAN (AUTO / MANUAL)
# UI: SCAN IMAGE (AUTO), SCAN IMAGE
# --------------------------------------------------
@app.route("/api/scan/image", methods=["POST"])
def scan_image():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No image file provided"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        file.save(tmp.name)
        path = tmp.name

    try:
        raw_result = shared.scan_image(path)
        safe_result = to_json_safe(raw_result)
        return jsonify({"result": safe_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(path)


# --------------------------------------------------
# ADVANCED IMAGE INVESTIGATION
# UI: ADV. INVESTIGATE IMG
# --------------------------------------------------
@app.route("/api/scan/image/advanced", methods=["POST"])
def scan_image_advanced():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No image file provided"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        file.save(tmp.name)
        path = tmp.name

    try:
        raw_result = shared.scan_image_advanced(path)
        safe_result = to_json_safe(raw_result)
        return jsonify({"result": safe_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(path)


# --------------------------------------------------
# VIDEO SCAN
# UI: SCAN VIDEO
# --------------------------------------------------
@app.route("/api/scan/video", methods=["POST"])
def scan_video():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No video file provided"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        file.save(tmp.name)
        path = tmp.name

    try:
        raw_result = shared.scan_video(path)
        safe_result = to_json_safe(raw_result)
        return jsonify({"result": safe_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(path)


# --------------------------------------------------
# ADVANCED VIDEO INVESTIGATION
# UI: ADV. INVESTIGATE VIDEO
# --------------------------------------------------
@app.route("/api/scan/video/advanced", methods=["POST"])
def scan_video_advanced():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No video file provided"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        file.save(tmp.name)
        path = tmp.name

    try:
        raw_result = shared.scan_video_advanced(path)
        safe_result = to_json_safe(raw_result)
        return jsonify({"result": safe_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(path)


# --------------------------------------------------
# AUDIO SCAN
# UI: SCAN AUDIO
# --------------------------------------------------
@app.route("/api/scan/audio", methods=["POST"])
def scan_audio():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        path = tmp.name

    try:
        raw_result = shared.scan_audio(path)
        safe_result = to_json_safe(raw_result)
        return jsonify({"result": safe_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(path)


# --------------------------------------------------
# FACE ENROLLMENT
# UI: ENROLL FACE
# --------------------------------------------------
@app.route("/api/face/enroll", methods=["POST"])
def enroll_face():
    file = request.files.get("file")
    identity = request.form.get("identity")

    if not file or not identity:
        return jsonify({"error": "Image and identity required"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        file.save(tmp.name)
        path = tmp.name

    try:
        raw_result = shared.enroll_face(path,identity)
        safe_result = to_json_safe(raw_result)
        return jsonify({"result": safe_result})

    except ValueError as e:
        # 👇 THIS IS IMPORTANT
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal enrollment failure"}), 500
    finally:
        os.remove(path)


# --------------------------------------------------
# GIT REPOSITORY SCAN
# UI: SCAN GIT REPO
# --------------------------------------------------
@app.route("/api/scan/git", methods=["POST"])
def scan_git():
    data = request.json
    repo_path = data.get("path")

    if not repo_path:
        return jsonify({"error": "Repository path required"}), 400

    try:
        raw_result = shared.scan_git_repo(repo_path)
        safe_result = to_json_safe(raw_result)
        return jsonify({"result": safe_result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# SERVER START
# --------------------------------------------------
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False  # keep false for judges
    )
