+++
title = "Thank you for your purchase"
slug = "thank-you"
+++

<div class="thankyou-hero">
  <div class="thankyou-inner">
    <h1>Thanks for supporting SilentGPT Dev Engine 🚀</h1>
    <p class="thankyou-subtitle">
      Your payment was successful. Your pack is ready to download.
    </p>

    <a id="download-link" class="thankyou-button">
      Download your pack
    </a>

    <p class="thankyou-hint">
      If the download doesn't start automatically, click the button above.
    </p>
  </div>
</div>

<script>
  (function() {
    const params = new URLSearchParams(window.location.search);
    const pack = params.get("pack");
    const sessionId = params.get("session_id");

    if (!pack || !sessionId) {
      console.warn("Missing pack or session_id in URL");
      return;
    }

    // Deine Backend-URL – wenn du sie änderst, hier anpassen:
    const backendBase = "https://silent-gpt-backend.onrender.com";
    const downloadUrl = `${backendBase}/download/${encodeURIComponent(pack)}?session_id=${encodeURIComponent(sessionId)}`;

    const link = document.getElementById("download-link");
    if (link) {
      link.href = downloadUrl;
    }

    // Optional: Auto-Download starten
    setTimeout(function() {
      window.location.href = downloadUrl;
    }, 1000);
  })();
</script>
