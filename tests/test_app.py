"""Basic smoke tests for the Reface AI Flask application."""

import io
import json
import time

import pytest

import app as application


@pytest.fixture()
def client():
    application.app.config["TESTING"] = True
    with application.app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Reface" in resp.data


def test_job_not_found(client):
    resp = client.get("/job/nonexistent-job-id")
    assert resp.status_code == 404
    data = json.loads(resp.data)
    assert "error" in data


def test_swap_image_missing_files(client):
    """Submitting without files should return 400."""
    resp = client.post("/swap/image", data={})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "error" in data


def test_swap_video_missing_files(client):
    """Submitting without files should return 400."""
    resp = client.post("/swap/video", data={})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert "error" in data


def test_swap_image_invalid_extension(client):
    """Uploading a file with a disallowed extension should return 400."""
    fake_file = (io.BytesIO(b"fake data"), "face.txt")
    resp = client.post(
        "/swap/image",
        data={"source": fake_file, "target": (io.BytesIO(b"fake"), "target.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_swap_image_creates_job(client, monkeypatch):
    """
    Posting valid image files returns a job_id and the job is accessible.
    We monkeypatch the background runner so no actual processing happens.
    """
    monkeypatch.setattr(application, "_run_job", lambda *a, **k: None)

    # Tiny 1x1 PNG bytes (valid image header)
    png_1x1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    resp = client.post(
        "/swap/image",
        data={
            "source": (io.BytesIO(png_1x1), "face.png"),
            "target": (io.BytesIO(png_1x1), "target.png"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "job_id" in data

    # Poll the job
    job_resp = client.get(f"/job/{data['job_id']}")
    assert job_resp.status_code == 200


def test_swap_video_creates_job(client, monkeypatch):
    """Posting valid files for a video job returns a job_id."""
    monkeypatch.setattr(application, "_run_job", lambda *a, **k: None)

    png_1x1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    # Minimal fake MP4 (wrong content but extension is valid)
    fake_mp4 = b"\x00\x00\x00\x14ftypisom" + b"\x00" * 100

    resp = client.post(
        "/swap/video",
        data={
            "source": (io.BytesIO(png_1x1), "face.png"),
            "target": (io.BytesIO(fake_mp4), "clip.mp4"),
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "job_id" in data
