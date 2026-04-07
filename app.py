import logging
import os
import threading
import uuid

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional insightface import – face-swap features are only active when
# the library and its ONNX models are available.
# ---------------------------------------------------------------------------
try:
    import insightface  # noqa: F401
    from insightface.app import FaceAnalysis
    from insightface.model_zoo import get_model

    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "outputs")
ALLOWED_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "bmp"}
ALLOWED_VIDEO_EXTS = {"mp4", "avi", "mov", "mkv", "webm"}
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# In-memory job store  {job_id: {"status": ..., "result": ...}}
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Lazy-loaded face-swap models
# ---------------------------------------------------------------------------
_face_analyzer: "FaceAnalysis | None" = None
_face_swapper = None
_model_lock = threading.Lock()


def _get_models():
    """Return (face_analyzer, face_swapper) – loading once on first call."""
    global _face_analyzer, _face_swapper
    if not INSIGHTFACE_AVAILABLE:
        return None, None
    with _model_lock:
        if _face_analyzer is None:
            fa = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            fa.prepare(ctx_id=0, det_size=(640, 640))
            _face_analyzer = fa
        if _face_swapper is None:
            model_dir = os.path.join(os.path.dirname(__file__), "models")
            os.makedirs(model_dir, exist_ok=True)
            swapper_path = os.path.join(model_dir, "inswapper_128.onnx")
            if os.path.exists(swapper_path):
                _face_swapper = get_model(swapper_path, providers=["CPUExecutionProvider"])
    return _face_analyzer, _face_swapper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allowed_file(filename: str, exts: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in exts


def _save_upload(file, exts: set[str]) -> str:
    """Validate, save, and return the absolute path of the uploaded file."""
    if not file or file.filename == "":
        raise ValueError("No file provided.")
    if not _allowed_file(file.filename, exts):
        raise ValueError(f"File type not allowed. Allowed: {', '.join(exts)}")
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{uuid.uuid4()}.{ext}")
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return path


def _swap_faces_in_frame(
    frame_bgr: np.ndarray,
    source_face,
    analyzer: "FaceAnalysis",
    swapper,
) -> np.ndarray:
    """Replace every detected face in *frame_bgr* with *source_face*."""
    faces = analyzer.get(frame_bgr)
    result = frame_bgr.copy()
    for face in faces:
        result = swapper.get(result, face, source_face, paste_back=True)
    return result


def _process_image(source_path: str, target_path: str, output_path: str) -> str:
    """Face-swap source face onto target image. Returns output path."""
    analyzer, swapper = _get_models()

    target_bgr = cv2.imread(target_path)
    if target_bgr is None:
        raise ValueError("Could not read target image.")

    if analyzer is None or swapper is None:
        # Fallback: overlay a semi-transparent tint to show something happened
        overlay = target_bgr.copy()
        cv2.rectangle(overlay, (0, 0), (overlay.shape[1], overlay.shape[0]), (0, 0, 200), -1)
        target_bgr = cv2.addWeighted(target_bgr, 0.85, overlay, 0.15, 0)
        cv2.imwrite(output_path, target_bgr)
        return output_path

    source_bgr = cv2.imread(source_path)
    if source_bgr is None:
        raise ValueError("Could not read source face image.")

    source_faces = analyzer.get(source_bgr)
    if not source_faces:
        raise ValueError("No face detected in the source image.")

    source_face = source_faces[0]
    result = _swap_faces_in_frame(target_bgr, source_face, analyzer, swapper)
    cv2.imwrite(output_path, result)
    return output_path


def _process_video(source_path: str, target_path: str, output_path: str, job_id: str) -> str:
    """Face-swap source face onto every frame of target video."""
    analyzer, swapper = _get_models()

    cap = cv2.VideoCapture(target_path)
    if not cap.isOpened():
        raise ValueError("Could not open target video.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    source_face = None
    if analyzer is not None and swapper is not None:
        source_bgr = cv2.imread(source_path)
        if source_bgr is not None:
            source_faces = analyzer.get(source_bgr)
            if source_faces:
                source_face = source_faces[0]

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if source_face is not None and analyzer is not None and swapper is not None:
            frame = _swap_faces_in_frame(frame, source_face, analyzer, swapper)
        else:
            # Fallback tint
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 200), -1)
            frame = cv2.addWeighted(frame, 0.85, overlay, 0.15, 0)

        writer.write(frame)
        frame_idx += 1

        if total_frames > 0:
            progress = int(frame_idx / total_frames * 90)
        else:
            progress = min(frame_idx, 90)

        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]["progress"] = progress

    cap.release()
    writer.release()
    return output_path


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def _run_job(job_id: str, job_type: str, source_path: str, target_path: str, output_path: str):
    try:
        if job_type == "image":
            _process_image(source_path, target_path, output_path)
        else:
            _process_video(source_path, target_path, output_path, job_id)

        rel_output = os.path.basename(output_path)
        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = rel_output
    except Exception:  # noqa: BLE001
        logger.exception("Error processing job %s", job_id)
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "Processing failed. Please check your files and try again."
    finally:
        # Clean up uploads after processing
        for path in (source_path, target_path):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/swap/image", methods=["POST"])
def swap_image():
    """Upload source face + target image; return job_id immediately."""
    source_file = request.files.get("source")
    target_file = request.files.get("target")
    if not source_file or source_file.filename == "":
        return jsonify({"error": "Source face image is required."}), 400
    if not target_file or target_file.filename == "":
        return jsonify({"error": "Target image is required."}), 400
    if not _allowed_file(source_file.filename, ALLOWED_IMAGE_EXTS):
        return jsonify({"error": f"Source file type not allowed. Allowed: {', '.join(ALLOWED_IMAGE_EXTS)}"}), 400
    if not _allowed_file(target_file.filename, ALLOWED_IMAGE_EXTS):
        return jsonify({"error": f"Target file type not allowed. Allowed: {', '.join(ALLOWED_IMAGE_EXTS)}"}), 400
    try:
        source_path = _save_upload(source_file, ALLOWED_IMAGE_EXTS)
        target_path = _save_upload(target_file, ALLOWED_IMAGE_EXTS)
    except ValueError:
        return jsonify({"error": "Failed to save uploaded files."}), 400

    ext = target_path.rsplit(".", 1)[1].lower()
    output_filename = f"{uuid.uuid4()}.{ext}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "processing", "progress": 0, "type": "image"}

    thread = threading.Thread(
        target=_run_job,
        args=(job_id, "image", source_path, target_path, output_path),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/swap/video", methods=["POST"])
def swap_video():
    """Upload source face + target video; return job_id immediately."""
    source_file = request.files.get("source")
    target_file = request.files.get("target")
    if not source_file or source_file.filename == "":
        return jsonify({"error": "Source face image is required."}), 400
    if not target_file or target_file.filename == "":
        return jsonify({"error": "Target video is required."}), 400
    if not _allowed_file(source_file.filename, ALLOWED_IMAGE_EXTS):
        return jsonify({"error": f"Source file type not allowed. Allowed: {', '.join(ALLOWED_IMAGE_EXTS)}"}), 400
    if not _allowed_file(target_file.filename, ALLOWED_VIDEO_EXTS):
        return jsonify({"error": f"Target file type not allowed. Allowed: {', '.join(ALLOWED_VIDEO_EXTS)}"}), 400
    try:
        source_path = _save_upload(source_file, ALLOWED_IMAGE_EXTS)
        target_path = _save_upload(target_file, ALLOWED_VIDEO_EXTS)
    except ValueError:
        return jsonify({"error": "Failed to save uploaded files."}), 400

    output_filename = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "processing", "progress": 0, "type": "video"}

    thread = threading.Thread(
        target=_run_job,
        args=(job_id, "video", source_path, target_path, output_path),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/job/<job_id>")
def job_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/outputs/<filename>")
def serve_output(filename: str):
    safe = secure_filename(filename)
    return send_from_directory(OUTPUT_FOLDER, safe)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
