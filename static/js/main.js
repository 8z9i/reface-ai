/* ── Tab switching ─────────────────────────────────────────────────────── */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(panel => {
      if (panel.id === `tab-${target}`) {
        panel.hidden = false;
        panel.classList.add('active');
      } else {
        panel.hidden = true;
        panel.classList.remove('active');
      }
    });
  });
});

/* ── Generic file-preview helper ──────────────────────────────────────── */
function bindFilePreview(inputId, previewId, cardId) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  const card = document.getElementById(cardId);

  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file) return;

    // Use FileReader to produce a data URL; check MIME prefix before
    // assigning to prevent non-media content reaching the DOM.
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target && event.target.result;
      if (typeof result === 'string' &&
          (result.startsWith('data:image/') || result.startsWith('data:video/'))) {
        preview.setAttribute('src', result);
        preview.hidden = false;
        card.classList.add('has-file');
        const label = card.querySelector('.upload-label');
        if (label) label.style.display = 'none';
        checkSubmitReady(input.closest('form'));
      }
    };
    reader.readAsDataURL(file);
  });

  // make the card clickable
  card.addEventListener('click', e => {
    if (e.target === input) return;
    input.click();
  });
}

function checkSubmitReady(form) {
  const inputs = form.querySelectorAll('input[type="file"]');
  const allFilled = [...inputs].every(inp => inp.files && inp.files.length > 0);
  const btn = form.querySelector('button[type="submit"]');
  if (btn) btn.disabled = !allFilled;
}

/* ── Bind image tab previews ────────────────────────────────────────────── */
bindFilePreview('src-img-input', 'src-img-preview', 'src-img-card');
bindFilePreview('tgt-img-input', 'tgt-img-preview', 'tgt-img-card');

/* ── Bind video tab previews ────────────────────────────────────────────── */
bindFilePreview('src-vid-input', 'src-vid-preview', 'src-vid-card');
bindFilePreview('tgt-vid-input', 'tgt-vid-preview', 'tgt-vid-card');

/* ── Job polling ──────────────────────────────────────────────────────── */
function pollJob(jobId, opts) {
  const { onProgress, onDone, onError } = opts;
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/job/${jobId}`);
      const data = await res.json();
      if (data.status === 'processing') {
        onProgress(data.progress || 0);
      } else if (data.status === 'done') {
        clearInterval(interval);
        onDone(data.result);
      } else if (data.status === 'error') {
        clearInterval(interval);
        onError(data.error || 'Unknown error');
      }
    } catch (err) {
      clearInterval(interval);
      onError(String(err));
    }
  }, 1000);
}

/* ── Image form submission ─────────────────────────────────────────────── */
document.getElementById('image-form').addEventListener('submit', async e => {
  e.preventDefault();

  const form = e.currentTarget;
  const progressWrap = document.getElementById('image-progress');
  const progressFill = document.getElementById('image-progress-fill');
  const progressLabel = document.getElementById('image-progress-label');
  const resultArea = document.getElementById('image-result');
  const resultImg = document.getElementById('image-result-img');
  const downloadBtn = document.getElementById('image-download-btn');
  const errorBox = document.getElementById('image-error');
  const submitBtn = document.getElementById('image-submit-btn');

  // Reset UI
  resultArea.hidden = true;
  errorBox.hidden = true;
  progressWrap.hidden = false;
  progressFill.style.width = '0%';
  progressLabel.textContent = 'Uploading…';
  submitBtn.disabled = true;

  try {
    const formData = new FormData(form);
    const res = await fetch('/swap/image', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || 'Upload failed');
    }

    progressLabel.textContent = 'Processing image…';

    pollJob(data.job_id, {
      onProgress(pct) {
        progressFill.style.width = `${pct}%`;
        progressLabel.textContent = `Processing… ${pct}%`;
      },
      onDone(filename) {
        progressWrap.hidden = true;
        const url = `/outputs/${filename}`;
        resultImg.src = url;
        downloadBtn.href = url;
        downloadBtn.download = filename;
        resultArea.hidden = false;
        submitBtn.disabled = false;
      },
      onError(msg) {
        progressWrap.hidden = true;
        errorBox.textContent = `Error: ${msg}`;
        errorBox.hidden = false;
        submitBtn.disabled = false;
      },
    });
  } catch (err) {
    progressWrap.hidden = true;
    errorBox.textContent = `Error: ${err.message}`;
    errorBox.hidden = false;
    submitBtn.disabled = false;
  }
});

/* ── Video form submission ─────────────────────────────────────────────── */
document.getElementById('video-form').addEventListener('submit', async e => {
  e.preventDefault();

  const form = e.currentTarget;
  const progressWrap = document.getElementById('video-progress');
  const progressFill = document.getElementById('video-progress-fill');
  const progressLabel = document.getElementById('video-progress-label');
  const resultArea = document.getElementById('video-result');
  const resultVid = document.getElementById('video-result-vid');
  const downloadBtn = document.getElementById('video-download-btn');
  const errorBox = document.getElementById('video-error');
  const submitBtn = document.getElementById('video-submit-btn');

  // Reset UI
  resultArea.hidden = true;
  errorBox.hidden = true;
  progressWrap.hidden = false;
  progressFill.style.width = '0%';
  progressLabel.textContent = 'Uploading video…';
  submitBtn.disabled = true;

  try {
    const formData = new FormData(form);
    const res = await fetch('/swap/video', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || 'Upload failed');
    }

    progressLabel.textContent = 'Processing frames…';

    pollJob(data.job_id, {
      onProgress(pct) {
        progressFill.style.width = `${pct}%`;
        progressLabel.textContent = `Processing frames… ${pct}%`;
      },
      onDone(filename) {
        progressWrap.hidden = true;
        const url = `/outputs/${filename}`;
        resultVid.src = url;
        downloadBtn.href = url;
        downloadBtn.download = filename;
        resultArea.hidden = false;
        submitBtn.disabled = false;
      },
      onError(msg) {
        progressWrap.hidden = true;
        errorBox.textContent = `Error: ${msg}`;
        errorBox.hidden = false;
        submitBtn.disabled = false;
      },
    });
  } catch (err) {
    progressWrap.hidden = true;
    errorBox.textContent = `Error: ${err.message}`;
    errorBox.hidden = false;
    submitBtn.disabled = false;
  }
});
