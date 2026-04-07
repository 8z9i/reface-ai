# Reface AI

AI-powered face swap web application that generates **images** and **videos** with a swapped face in seconds.

## Features

- 🖼️ **Image Reface** – upload a source face and a target image; get a new image with the face replaced.
- 🎬 **Video Reface** – upload a source face and a target video; every frame is processed to replace detected faces.
- ⚡ Async job processing with a live progress bar.
- 🖥️ Clean dark-themed web UI – no account required.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · Flask |
| Face detection / swap | InsightFace (`buffalo_l` + `inswapper_128`) |
| Video processing | OpenCV |
| Frontend | Vanilla HTML / CSS / JS |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Download the inswapper_128.onnx model
#    Place it at:  models/inswapper_128.onnx
#    Download from: https://huggingface.co/datasets/Gourieff/ReActor/tree/main/models/inswapper_128.onnx

# 3. Run the server
python app.py
```

Then open http://localhost:5000 in your browser.

> **Note:** Without `models/inswapper_128.onnx` the app still runs but applies a
> simple colour-tint overlay instead of a real face swap (useful for testing the UI).

## Project Layout

```
reface-ai/
├── app.py               # Flask application & processing logic
├── requirements.txt     # Python dependencies
├── models/              # Place inswapper_128.onnx here (not committed)
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    └── index.html
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Web UI |
| `POST` | `/swap/image` | Submit image face-swap job (`multipart/form-data`: `source`, `target`) |
| `POST` | `/swap/video` | Submit video face-swap job (`multipart/form-data`: `source`, `target`) |
| `GET` | `/job/<job_id>` | Poll job status (`status`, `progress`, `result`) |
| `GET` | `/outputs/<filename>` | Download processed output file |
