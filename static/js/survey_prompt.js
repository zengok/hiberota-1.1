(() => {
  const STORAGE_KEY = "hiberota:grant-survey-seen:v1";
  const PROMPT_DELAY_MS = 4500;

  const shouldSkipPrompt = () => {
    if (window.location.pathname.startsWith("/hibe-anketi/")) {
      return true;
    }
    try {
      return window.localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return true;
    }
  };

  const rememberPrompt = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      return;
    }
  };

  const closePrompt = (prompt) => {
    prompt.remove();
    rememberPrompt();
  };

  const showPrompt = () => {
    if (shouldSkipPrompt() || document.querySelector("[data-survey-prompt]")) {
      return;
    }

    const prompt = document.createElement("aside");
    prompt.className = "survey-prompt";
    prompt.setAttribute("data-survey-prompt", "");
    prompt.setAttribute("aria-label", "Hibe anketi daveti");
    prompt.innerHTML = `
      <div>
        <p class="fw-semibold mb-1">Size uygun çağrıları bulun</p>
        <p class="text-secondary small mb-0">Kısa anketle hedef kitlenize uygun hibe çağrılarını eşleştirin.</p>
      </div>
      <div class="survey-prompt-actions">
        <a class="btn btn-primary btn-sm" href="/hibe-anketi/">Ankete git</a>
        <button class="btn btn-outline-secondary btn-sm" type="button">Atla</button>
      </div>
    `;
    prompt.querySelector("button")?.addEventListener("click", () => closePrompt(prompt));
    prompt.querySelector("a")?.addEventListener("click", rememberPrompt);
    document.body.append(prompt);
  };

  document.addEventListener("DOMContentLoaded", () => {
    window.setTimeout(showPrompt, PROMPT_DELAY_MS);
  });
})();
