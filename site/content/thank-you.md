+++
title = ""
slug = "thank-you"
+++

{{< rawhtml >}}
<style>
.thankyou-outer {
  min-height: 50vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 2vh;
  padding-bottom: 2rem;
}

.thankyou-wrapper {
  width: 100%;
  max-width: 680px;
}

.thankyou-card {
  background: var(--bg-alt);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 2.25rem 2rem;
  text-align: center;
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.45);
}

/* Success icon */

.thankyou-icon-circle {
  width: 64px;
  height: 64px;
  margin: 0 auto 1.5rem;
  border-radius: 50%;
  border: 2px solid #22c55e;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.1);
  animation: ty-pop-in 0.6s ease-out;
}

.thankyou-icon-check {
  width: 24px;
  height: 12px;
  border-left: 3px solid #22c55e;
  border-bottom: 3px solid #22c55e;
  transform: rotate(-45deg);
}

@keyframes ty-pop-in {
  0% {
    transform: scale(0.7);
    opacity: 0;
  }
  60% {
    transform: scale(1.05);
    opacity: 1;
  }
  100% {
    transform: scale(1);
  }
}

/* Text */

.thankyou-title {
  font-size: 1.9rem;
  margin-bottom: 0.75rem;
}

.ty-pack-name {
  color: #a5b4fc;
}

.thankyou-subtitle {
  color: var(--muted);
  margin-bottom: 1.1rem;
  font-size: 1.02rem;
  line-height: 1.5;
}

.thankyou-subtitle-small {
  color: var(--muted);
  font-size: 0.9rem;
  margin-bottom: 1.4rem;
}

/* Button & progress */

.thankyou-download-btn {
  display: inline-block;
  padding: 0.8rem 1.9rem;
  background: linear-gradient(135deg, var(--accent), #22c55e);
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
  text-decoration: none;
  margin-bottom: 1rem;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.7);
}

.thankyou-download-btn:hover {
  filter: brightness(1.05);
}

.thankyou-progress {
  margin: 0.75rem auto 0.5rem;
  max-width: 260px;
  height: 6px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.25);
  overflow: hidden;
}

.thankyou-progress-bar {
  width: 0%;
  height: 100%;
  background: linear-gradient(135deg, var(--accent), #22c55e);
  animation: ty-progress-fill 1s ease-out forwards;
}

@keyframes ty-progress-fill {
  from { width: 0%; }
  to   { width: 100%; }
}

/* Redirect info */

.thankyou-hint {
  font-size: 0.9rem;
  color: var(--muted);
  margin-top: 0.5rem;
}

.thankyou-redirect {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: var(--muted);
}

.thankyou-link-btn {
  background: none;
  border: none;
  padding: 0;
  margin-left: 0.35rem;
  color: var(--accent);
  font-size: 0.9rem;
  cursor: pointer;
}

.thankyou-link-btn:hover {
  text-decoration: underline;
}

/* A/B Variant */

#ty-root[data-variant="B"] .thankyou-card {
  background: radial-gradient(circle at top, #020617 0, #000 100%);
  border-color: rgba(148, 163, 184, 0.4);
}

#ty-root[data-variant="B"] .thankyou-download-btn {
  background: linear-gradient(135deg, #22c55e, #0ea5e9);
}

@media (max-width: 720px) {
  .thankyou-card {
    padding: 1.8rem 1.4rem;
  }
  .thankyou-title {
    font-size: 1.5rem;
  }
}
</style>

<div id="ty-root" class="thankyou-outer">
  <div class="thankyou-wrapper">
    <div class="thankyou-card">
      <div class="thankyou-icon-circle">
        <div class="thankyou-icon-check"></div>
      </div>

      <h1 class="thankyou-title">
        Thank you for your purchase&nbsp;
        <span id="pack-name" class="ty-pack-name">your SilentGPT pack</span> 🚀
      </h1>

      <p id="pack-message" class="thankyou-subtitle">
        Your payment was successful and your pack is ready to download.
      </p>

      <p class="thankyou-subtitle-small">
        Confirmation for:
        <span id="pack-slug">–</span>
      </p>

      <a id="download-link" class="thankyou-download-btn">
        Download your pack
      </a>

      <div class="thankyou-progress">
        <div class="thankyou-progress-bar"></div>
      </div>

      <p class="thankyou-hint">
        If the download doesn't start automatically, click the button above.
      </p>

      <p id="redirect-row" class="thankyou-redirect">
        You'll be redirected back to the blog in
        <span id="redirect-counter">20</span> seconds.
        <button id="redirect-cancel" type="button" class="thankyou-link-btn">
          Stay here
        </button>
      </p>
    </div>
  </div>
</div>

<script>
(function () {
  const params = new URLSearchParams(window.location.search);
  const pack = params.get("pack");
  const sessionId = params.get("session_id");

  const PACKS = {
    "ai-rag-pack-1": {
      name: "AI & RAG Troubleshooting Pack #1",
      message:
        "Perfect if you're building retrieval-augmented generation systems and want battle-tested patterns for debugging, monitoring and improving RAG pipelines."
    },
    "fastapi-backend-pack-1": {
      name: "FastAPI Backend Pack #1",
      message:
        "Great choice for shipping production-ready FastAPI services faster – with patterns for routing, settings, background jobs and deployments."
    },
    "python-data-pack-1": {
      name: "Python Data Engineering Pack #1",
      message:
        "Ideal if you automate data workflows in Python – from cleaning and validation to reporting and small in-house tools."
    },
    "devops-docker-pack-1": {
      name: "DevOps & Docker Pack #1",
      message:
        "A solid companion for containerising and deploying your services with Docker and modern DevOps practices."
    },
    "testing-pack-1": {
      name: "Testing & Pytest Pack #1",
      message:
        "Great pick if you want more reliable Python code with structured tests, fixtures and CI-friendly patterns."
    },
    _default: {
      name: "your SilentGPT pack",
      message:
        "Your payment was successful and your digital pack is ready to download."
    }
  };

  const packInfo = PACKS[pack] || PACKS._default;

  const nameEl = document.getElementById("pack-name");
  const msgEl = document.getElementById("pack-message");
  const slugEl = document.getElementById("pack-slug");
  if (nameEl) nameEl.textContent = packInfo.name;
  if (msgEl) msgEl.textContent = packInfo.message;
  if (slugEl) slugEl.textContent = pack || "–";

  // A/B Variante
  const root = document.getElementById("ty-root");
  const variant = Math.random() < 0.5 ? "A" : "B";
  if (root) root.dataset.variant = variant;

  // Download handling
  if (!pack || !sessionId) {
    console.warn("Missing pack or session_id in URL");
    const link = document.getElementById("download-link");
    if (link) {
      link.textContent = "Error: missing download information";
      link.removeAttribute("href");
    }
    return;
  }

  const backendBase = "https://silent-gpt-backend.onrender.com";
  const downloadUrl =
    backendBase +
    "/download/" +
    encodeURIComponent(pack) +
    "?session_id=" +
    encodeURIComponent(sessionId);

  const link = document.getElementById("download-link");
  if (link) link.href = downloadUrl;

  // Auto-Download
  setTimeout(function () {
    window.location.href = downloadUrl;
  }, 1000);

  // Redirect zurück zum Blog
  const redirectTotal = 20;
  let remaining = redirectTotal;
  let cancelled = false;

  const counterEl = document.getElementById("redirect-counter");
  const rowEl = document.getElementById("redirect-row");
  const cancelBtn = document.getElementById("redirect-cancel");
  if (counterEl) counterEl.textContent = String(remaining);

  const timer = setInterval(function () {
    if (cancelled) {
      clearInterval(timer);
      return;
    }
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(timer);
      if (!cancelled) window.location.href = "/blog/";
    } else if (counterEl) {
      counterEl.textContent = String(remaining);
    }
  }, 1000);

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      cancelled = true;
      if (rowEl) {
        rowEl.textContent =
          "You’ll stay on this page. Feel free to explore your new pack!";
      }
    });
  }
})();
</script>
{{< /rawhtml >}}
