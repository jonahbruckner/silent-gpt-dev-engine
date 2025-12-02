+++
title = "Thank you for your purchase"
slug = "thank-you"
date = 2025-12-02T00:00:00Z
+++

<div class="section">
<div class="container thankyou-wrapper">
<div class="thankyou-card">

<h1 class="thankyou-title">Thank you for your purchase 🚀</h1>

<p class="thankyou-subtitle">
  Thanks for supporting SilentGPT Dev Engine.
  Your payment was successful and your pack is ready to download.
</p>

<a id="download-link" class="thankyou-download-btn">
  Download your pack
</a>

<p class="thankyou-hint">
  If the download doesn’t start automatically, click the button above.
</p>

</div>
</div>
</div>

<script>
  (function () {
    const params = new URLSearchParams(window.location.search);
    const pack = params.get("pack");
    const sessionId = params.get("session_id");

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
    if (link) {
      link.href = downloadUrl;
    }

    // Auto-Download nach kurzer Pause
    setTimeout(function () {
      window.location.href = downloadUrl;
    }, 1000);
  })();
</script>
