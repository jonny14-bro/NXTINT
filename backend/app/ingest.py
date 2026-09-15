import os
import cv2
import tempfile
import re
import math
from typing import Optional, List
from insightface.app import FaceAnalysis
import base64
from collections import Counter
import numpy as np


from PIL import Image
import piexif
import imagehash

# ------------------ MODEL CACHES ------------------
_CLIP_MODEL = None
_TEXT_MODEL = None
_YOLO_MODEL = None
_VOSK_MODEL = None
_INSIGHTFACE_APP = None

def _load_insightface_app():
    global _INSIGHTFACE_APP
    if _INSIGHTFACE_APP is None:
        app = FaceAnalysis(name="buffalo_l")
        app.prepare(ctx_id=-1, det_size=(640, 640))
        _INSIGHTFACE_APP = app
    return _INSIGHTFACE_APP

def identify_face(matches, threshold=0.5):
    if not matches:
        return "UNKNOWN", 0.0, None

    uid, dist, meta = matches[0]
    confidence = round(max(0.0, min(1.0, 1 - dist)) * 100, 2)

    if confidence < threshold * 100:
        return "UNKNOWN", confidence, meta

    identity = meta.get("identity")
    if not identity:
        return "UNKNOWN", confidence, meta

    return identity, confidence, meta

def _load_vosk(model_path="models/vosk-model-small-en-us-0.15"):
    global _VOSK_MODEL
    if _VOSK_MODEL is None:
        try:
            from vosk import Model
            _VOSK_MODEL = Model(model_path)
        except Exception:
            _VOSK_MODEL = None
    return _VOSK_MODEL

def _load_clip():
    global _CLIP_MODEL
    if _CLIP_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _CLIP_MODEL = SentenceTransformer('clip-ViT-B-32')
        except Exception:
            _CLIP_MODEL = None
    return _CLIP_MODEL


def _load_text_model():
    global _TEXT_MODEL
    if _TEXT_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _TEXT_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            _TEXT_MODEL = None
    return _TEXT_MODEL


def _load_yolo():
    global _YOLO_MODEL
    if _YOLO_MODEL is None:
        try:
            from ultralytics import YOLO
            _YOLO_MODEL = YOLO("yolov8n.pt")
        except Exception:
            _YOLO_MODEL = None
    return _YOLO_MODEL


# ------------------ EXIF ------------------
def extract_exif(path: str) -> dict:
    result = {}
    try:
        img = Image.open(path)
        exif_data = img._getexif() or {}

        try:
            exif_ifd = piexif.load(path)
            result['piexif'] = exif_ifd
        except:
            result['piexif'] = None

        result['raw_exif'] = exif_data
        gps = _extract_gps(result['piexif'], exif_data)
        if gps:
            result['gps'] = gps

    except Exception as e:
        result['error'] = str(e)
    return result


def _extract_gps(piexif_data, raw_exif) -> Optional[dict]:
    try:
        if piexif_data and 'GPS' in piexif_data:
            gps = piexif_data['GPS']
            if not gps:
                return None

            def _to_deg(v):
                return v[0][0]/v[0][1] + v[1][0]/v[1][1]/60 + v[2][0]/v[2][1]/3600

            lat = _to_deg(gps.get(piexif.GPSIFD.GPSLatitude))
            lon = _to_deg(gps.get(piexif.GPSIFD.GPSLongitude))

            lat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
            lon_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()

            if lat_ref != 'N': lat = -lat
            if lon_ref != 'E': lon = -lon

            return {"lat": lat, "lon": lon}
    except:
        pass
    return None


# ------------------ IMAGE EMBEDDING ------------------
def compute_image_embedding(path: str) -> List[float]:
    model = _load_clip()
    if model is not None:
        try:
            img = Image.open(path).convert('RGB')
            return model.encode(img, convert_to_numpy=True).tolist()
        except:
            pass

    try:
        phash = imagehash.phash(Image.open(path))
        h = int(str(phash), 16)
        return [(h >> i) & 0xFFFF for i in range(0, 128, 16)]
    except:
        return []


# ------------------ VIDEO FRAMES ------------------
def extract_frames(video_path: str, out_dir: Optional[str] = None, fps: int = 1) -> List[str]:
    import cv2

    if out_dir is None:
        out_dir = tempfile.mkdtemp(prefix='frames_')

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video")

    fps_video = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(1, int(fps_video / fps))

    saved = []
    idx = 0
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if idx % step == 0:
            path = os.path.join(out_dir, f"frame_{count:05d}.jpg")
            cv2.imwrite(path, frame)
            saved.append(path)
            count += 1
        idx += 1

    cap.release()
    return saved


# ------------------GIT SECRET SCANNER ------------------

def deduplicate_findings(findings):
    seen = set()
    unique = []

    for f in findings:
        key = (
            f.get("file"),
            f.get("type"),
            f.get("match")
        )
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique

def scan_git_repo_for_secrets(repo_path: str) -> List[dict]:
    findings = []

    SECRET_PATTERNS = {
        "JWT Token": {
            "regex": r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.?[A-Za-z0-9_-]*',
            "severity": "High"
        },
        "Private Key": {
            "regex": r'-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----',
            "severity": "Critical"
        },
        "OAuth Secret": {
            "regex": r'(client_secret|oauth_secret|clientSecret)\s*[:=]\s*[A-Za-z0-9\-_]{8,}',
            "severity": "Critical"
        },
        "API Key": {
            "regex": r'API[_-]?KEY\s*[=:]\s*["\']?.{16,}',
            "severity": "Critical"
        },
        "Password": {
            "regex": r'(password|passwd|pwd)\s*[=:]\s*["\']?.{6,}',
            "severity": "High"
        }
    }

    compiled = {
        name: {
            "regex": re.compile(cfg["regex"], re.I),
            "severity": cfg["severity"]
        }
        for name, cfg in SECRET_PATTERNS.items()
    }

    BASE64_REGEX = re.compile(
        r'(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{40,}={0,2})(?![A-Za-z0-9+/=])'
    )

    for root, _, files in os.walk(repo_path):
        for fname in files:
            path = os.path.join(root, fname)

            if fname.lower().endswith((
                ".png", ".jpg", ".jpeg", ".gif", ".zip",
                ".exe", ".mp4", ".pdf", ".wasm",
                ".ico", ".woff", ".ttf"
            )):
                continue

            try:
                with open(path, "r", errors="ignore") as f:
                    data = f.read()

                # -------------------------------------------------
                # 1️⃣ STANDARD SECRET PATTERNS
                # -------------------------------------------------
                has_private_key = False

                for stype, cfg in compiled.items():
                    for m in cfg["regex"].finditer(data):
                        findings.append({
                            "file": path,
                            "type": stype,
                            "match": m.group(0),
                            "severity": cfg["severity"]
                        })

                        if stype == "Private Key":
                            has_private_key = True

                # -------------------------------------------------
                # 2️⃣ SMART BASE64 DETECTION (SKIP IF PRIVATE KEY)
                # -------------------------------------------------
                if not has_private_key:
                    for m in BASE64_REGEX.finditer(data):
                        start = max(0, m.start() - 120)
                        end = min(len(data), m.end() + 120)
                        context = data[start:end]

                        res = analyze_base64_candidate(m.group(0), context, path)
                        if res:
                            severity = (
                                "High" if res["type"] == "JWT Token" else "Medium"
                            )

                            findings.append({
                                "file": path,
                                "type": res["type"],
                                "match": m.group(0)[:120],
                                "severity": severity,
                                "entropy": res["entropy"],
                                "decoded_preview": res["preview"]
                            })

            except Exception:
                pass

    # -------------------------------------------------
    # 3️⃣ FINAL DEDUPLICATION
    # -------------------------------------------------
    return deduplicate_findings(findings)




def clean_secret_findings(raw, repo_url=None):
    clean = []
    for item in raw:
        fp = item.get("file", "").lower()
        if any(x in fp for x in IGNORED_PATHS):
            continue

        clean.append({
            "repo": repo_url,
            "file": item["file"],
            "type": item["type"],
            "leak": item["match"][:120],
            "severity": item["severity"],
            "entropy": item.get("entropy")
        })
    return clean




def scan_git_repo_for_secrets_with_reports(repo_path, repo_url=None):
    raw = scan_git_repo_for_secrets(repo_path)
    return {"raw_findings": raw, "clean_report": clean_secret_findings(raw, repo_url)}


# ------------------ YOLO OBJECT DETECTION ------------------
def detect_objects_in_image(image_path, conf_thresh=0.25):
    model = _load_yolo()
    if model is None:
        return [{"error": "YOLO not available"}]

    results = model(image_path)
    detections = []

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf < conf_thresh:
                continue

            cls_id = int(box.cls[0])
            label = model.names.get(cls_id, str(cls_id))
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detections.append({
                "label": label,
                "confidence": round(conf, 4),
                "bbox": [x1, y1, x2, y2]
            })

    return detections


# ------------------ INSIGHT RECTINA FACE & ARCFACE (face embeddings) ------------------


def detect_faces_in_image(image_path, conf_thresh=0.25):
    app = _load_insightface_app()
    img = Image.open(image_path).convert("RGB")
    import numpy as np

    img_np = np.asarray(img)
    faces = app.get(img_np)

    detections = []
    for f in faces:
        if f.det_score < conf_thresh:
            continue

        x1, y1, x2, y2 = map(int, f.bbox)
        detections.append({
            "label": "face",
            "confidence": round(float(f.det_score), 4),
            "bbox": [x1, y1, x2, y2],
            "embedding": f.embedding.tolist()
        })

    return detections



def crop_face(image_path, bbox):
    """Crop a face bbox from an image and return a PIL Image (RGB)."""
    from PIL import Image
    img = Image.open(image_path).convert('RGB')
    x1, y1, x2, y2 = bbox
    w, h = img.size
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w - 1))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h - 1))
    return img.crop((x1, y1, x2, y2))


def process_image_faces(image_path, conf_thresh=0.25):
    from backend.app.ingest import extract_exif

    exif = extract_exif(image_path)
    gps = exif.get("gps")

    dets = detect_faces_in_image(image_path, conf_thresh=conf_thresh)
    faces = []

    for d in dets:
        if 'error' in d:
            continue

        bbox = d['bbox']
        crop = crop_face(image_path, bbox)
        emb = d.get("embedding")

        face = {
            'bbox': bbox,
            'confidence': d.get('confidence'),
            'embedding': emb,
            'crop': crop
        }

        # ✅ attach GPS only if available
        if gps:
            face["gps"] = gps

        faces.append(face)

    return faces



def process_video_faces(video_path, fps=1, conf_thresh=0.25):
    """Extract frames from a video and run face detection/embedding on each frame.

    Returns a list of dicts: {'frame','file','bbox','confidence','embedding','crop'}
    """
    frames = extract_frames(video_path, fps=fps)
    results = []
    for idx, fpath in enumerate(frames):
        for face in process_image_faces(fpath, conf_thresh=conf_thresh):
            results.append({'frame': idx, 'file': fpath, **face})
    return results


def ingest_faces_to_faiss(image_path, faiss_manager, source: str = "", file_hash: Optional[str] = None, conf_thresh=0.25):
    """Detect faces in `image_path`, compute embeddings and insert them into `faiss_manager`.

    If `faiss_manager` exposes `add_face(...)` that will be used (better for `FaceFaissManager`), otherwise falls back to `add(...)`.

    Returns list of uids added.
    """
    faces = process_image_faces(image_path, conf_thresh=conf_thresh)
    uids = []
    for f in faces:
        emb = f.get('embedding') or []
        if not emb:
            continue
        try:
            # prefer face-specific API when present
            add_func = getattr(faiss_manager, 'add_face')
            uid = add_func(emb, source=source, bbox=f.get('bbox'), file_hash=file_hash)
        except Exception:
            uid = faiss_manager.add(emb, metadata={'source': source, 'bbox': f.get('bbox'), 'gps': f.get('gps'), 'file': image_path}, file_hash=file_hash)
        uids.append(uid)
    return uids


# ------------------ TEXT OSINT ------------------
def analyze_text_osint(text: str) -> dict:
    return {
        "emails": re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text),
        "phones": re.findall(r"\+?\d[\d -]{8,12}\d", text),
        "usernames": re.findall(r"@[\w_]+", text),
        "possible_credentials": re.findall(r"(password|passwd|pwd)[\s:=]+[\S]+", text, re.I)
    }


def compute_text_embedding(text: str) -> list:
    model = _load_text_model()
    if model:
        return model.encode(text).tolist()
    return []


# ------------------ AUDIO ------------------
def analyze_audio(path: str) -> dict:
    result = {
        "transcript": None,
        "environment": [],
        "spectral_features": {},
        "engine": "vosk-offline"
    }

    try:
        import librosa
        import numpy as np
        import soundfile as sf
        from vosk import KaldiRecognizer
        import json

        # Load audio
        y, sr_rate = librosa.load(path, sr=16000, mono=True)

        # Spectral features (unchanged)
        result["spectral_features"] = {
            "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr_rate))),
            "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(y)))
        }

        # Environment inference
        if result["spectral_features"]["spectral_centroid"] > 2500:
            result["environment"].append("Urban / Traffic Noise")
        else:
            result["environment"].append("Indoor / Quiet")

        # Load Vosk model
        model = _load_vosk()
        if model is None:
            result["transcript"] = "[VOSK MODEL NOT AVAILABLE]"
            return result

        # Write temp WAV (Vosk requires WAV stream)
        tmp_wav = path + ".vosk.wav"
        sf.write(tmp_wav, y, sr_rate)

        rec = KaldiRecognizer(model, sr_rate)
        rec.SetWords(True)

        transcript = ""

        with open(tmp_wav, "rb") as f:
            while True:
                data = f.read(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part = json.loads(rec.Result()).get("text", "")
                    transcript += " " + part

        final = json.loads(rec.FinalResult()).get("text", "")
        transcript += " " + final

        result["transcript"] = transcript.strip() or None

        os.remove(tmp_wav)

    except Exception as e:
        result["error"] = str(e)

    return result
    
    
    
   
SECRET_CONTEXT_WORDS = [
    "key", "secret", "token", "password",
    "auth", "authorization", "apikey",
    "api_key", "jwt", "bearer"
]

IGNORED_PATHS = [
    "node_modules", "package-lock.json",
    "yarn.lock", "pnpm-lock.yaml",
    ".min.js", "dist", "vendor"
]


def shannon_entropy_bytes(data: bytes) -> float:
    if not data:
        return 0.0
    freq = Counter(data)
    probs = [c / len(data) for c in freq.values()]
    return -sum(p * math.log2(p) for p in probs)


def analyze_base64_candidate(b64: str, context: str, file_path: str):
    file_path = file_path.lower()

    if any(p in file_path for p in IGNORED_PATHS):
        return None

    try:
        decoded = base64.b64decode(b64, validate=True)
    except Exception:
        return None

    entropy = shannon_entropy_bytes(decoded)
    if entropy < 4.5:
        return None

    ctx = context.lower()
    if not any(k in ctx for k in SECRET_CONTEXT_WORDS):
        return None

    secret_type = "Encoded Secret"
    if decoded.count(b".") == 2 or b'"alg"' in decoded:
        secret_type = "JWT Token"
    elif decoded.strip().startswith(b"{"):
        secret_type = "Encoded JSON Secret"

    return {
        "type": secret_type,
        "entropy": round(entropy, 2),
        "preview": decoded[:40].decode(errors="ignore")
    }



def scan_text_for_secrets(text: str, source: str = "<text-file>") -> List[dict]:
    findings = []
    seen = set()

    SECRET_PATTERNS = {
        "JWT Token": {
            "regex": r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.?[A-Za-z0-9_-]*',
            "severity": "High"
        },
        "API Key": {
            "regex": r'api[_-]?key\s*[=:]\s*["\']?.{16,}',
            "severity": "Critical"
        },
        "Password": {
            "regex": r'(password|passwd|pwd)\s*[=:]\s*["\']?.{6,}',
            "severity": "High"
        }
    }

    compiled = {
        k: {
            "regex": re.compile(v["regex"], re.I),
            "severity": v["severity"]
        }
        for k, v in SECRET_PATTERNS.items()
    }

    BASE64_REGEX = re.compile(
        r'(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{40,}={0,2})(?![A-Za-z0-9+/=])'
    )

    # -------- pattern matches --------
    for stype, cfg in compiled.items():
        for m in cfg["regex"].finditer(text):
            key = (stype, m.group(0))
            if key in seen:
                continue
            seen.add(key)

            findings.append({
                "source": source,
                "type": stype,
                "leak": m.group(0)[:120],
                "severity": cfg["severity"]
            })

    # -------- base64 + entropy --------
    for m in BASE64_REGEX.finditer(text):
        context = text[max(0, m.start()-120):m.end()+120]
        res = analyze_base64_candidate(m.group(0), context, source)
        if not res:
            continue

        key = ("base64", m.group(0))
        if key in seen:
            continue
        seen.add(key)

        findings.append({
            "source": source,
            "type": res["type"],
            "leak": m.group(0)[:120],
            "severity": "High" if res["type"] == "JWT Token" else "Medium",
            "entropy": res["entropy"]
        })

    return findings

# ADD IMAGES FILTERED TO THE DATABASE

def annotate_image_faces(image_path, faces, output_path):
    import cv2

    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError("Failed to load image")

    for face in faces:
        x1, y1, x2, y2 = face["bbox"]
        fid = f"{face['identity']} ({face['confidence']}%)"

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            img,
            fid,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    success = cv2.imwrite(output_path, img)
    if not success:
        raise RuntimeError(f"Failed to write annotated image to {output_path}")

# ADD INMAGES OR FRAME TO THE DATABASE
def save_best_identity_frame(uid, image_path, bbox):
    # ---- HARD TYPE GUARDS ----
    if isinstance(image_path, list):
        if not image_path:
            raise ValueError("Empty image_path list")
        image_path = image_path[0]

    if not isinstance(image_path, (str, bytes, os.PathLike)):
        raise TypeError(
            f"image_path must be a path, got {type(image_path)}"
        )

    # normalize bbox
    if isinstance(bbox, list) and len(bbox) == 1:
        bbox = bbox[0]

    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError("bbox must be [x1, y1, x2, y2]")

    x1, y1, x2, y2 = map(int, bbox)


    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Failed to read image: {image_path}")

    h, w = img.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    face_crop = img[y1:y2, x1:x2]
    if face_crop.size == 0:
        raise RuntimeError("Empty face crop")

    out_dir = os.path.join("faces", str(uid))
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, "best.jpg")
    cv2.imwrite(out_path, face_crop)

    return out_path




# ADD ADVANCED VIDEO ANALYSIS

def process_video_faces_advanced(video_path, face_faiss, min_frames=2, conf_thresh=50):
    import numpy as np
    from backend.app.ingest import extract_frames, process_image_faces
    from ui import identify_face   # adjust import if needed

    frames = extract_frames(video_path, fps=5)

    identity_hits = {}

    for frame_idx, frame_path in enumerate(frames):
        faces = process_image_faces(frame_path, conf_thresh=0.30)

        for face in faces:
            emb = face.get("embedding")
            if not emb:
                continue

            vec = np.asarray(emb, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm == 0:
                continue
            vec /= norm

            matches = face_faiss.search_by_vector(vec.tolist(), k=3)

            identity, confidence, _ = identify_face(matches)

            # 🚨 CRITICAL FIX: ignore UNKNOWN
            if identity == "UNKNOWN" or confidence < conf_thresh:
                continue

            # -----------------------------
            # TRACK IDENTITY ACROSS FRAMES
            # -----------------------------
            entry = identity_hits.get(identity)

            if not entry:
                identity_hits[identity] = {
                    "frames_seen": 1,
                    "best_confidence": confidence,
                    "best_frame": frame_path,
                    "bbox": face.get("bbox"),
                }
            else:
                entry["frames_seen"] += 1
                if confidence > entry["best_confidence"]:
                    entry["best_confidence"] = confidence
                    entry["best_frame"] = frame_path
                    entry["bbox"] = face.get("bbox")

    # -----------------------------
    # CONFIRM IDENTITIES
    # -----------------------------
    confirmed = {
        identity: data
        for identity, data in identity_hits.items()
        if data["frames_seen"] >= min_frames
    }

    return confirmed




'''
def identify_face(matches, threshold=0.6):
    """
    matches: list of (uid, distance, metadata)
    """
    if not matches:
        return "UNKNOWN", 0, None

    uid, dist, meta = matches[0]
    confidence = round(max(0.0, min(1.0, 1 - dist)) * 100, 2)

    if confidence < threshold * 100:
        return "UNKNOWN", confidence, None

    label = meta.get("label") or meta.get("source") or "KNOWN_FACE"
    return label, confidence, uid

'''

#--------------------------------------------
# ASSIGN FACE ID IN ADVANCED VIDEO/IMAGE SCAN
#--------------------------------------------

def assign_face_ids(faces):
    """
    Assign stable FACE_001, FACE_002, ... IDs to detected faces.
    """
    for idx, face in enumerate(faces, start=1):
        face["face_id"] = f"FACE_{idx:03d}"
    return faces


def extract_media_metadata_ffprobe(path: str) -> dict:
    """
    Extract forensic metadata from video/audio using ffprobe.
    Safe (read-only).
    """
    import subprocess, json

    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

        meta = {
            "format": data.get("format", {}),
            "streams": []
        }

        for s in data.get("streams", []):
            meta["streams"].append({
                "codec_type": s.get("codec_type"),
                "codec_name": s.get("codec_name"),
                "width": s.get("width"),
                "height": s.get("height"),
                "rotation": s.get("tags", {}).get("rotate"),
                "creation_time": s.get("tags", {}).get("creation_time"),
                "location": (
                    s.get("tags", {}).get("location") or
                    s.get("tags", {}).get("com.apple.quicktime.location.ISO6709")
                )
            })

        return meta

    except Exception as e:
        return {"error": str(e)}

