(() => {
  const STORAGE_KEY = "hiberota:favorites";
  const MAX_FAVORITES = 200;

  const readFavorites = () => {
    try {
      const rawValue = window.localStorage.getItem(STORAGE_KEY);
      const parsed = rawValue ? JSON.parse(rawValue) : [];
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed
        .map((item) => Number.parseInt(String(item), 10))
        .filter((item) => Number.isInteger(item) && item > 0)
        .slice(0, MAX_FAVORITES);
    } catch {
      return [];
    }
  };

  const writeFavorites = (favorites) => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify([...new Set(favorites)].slice(0, MAX_FAVORITES)));
  };

  const setButtonState = (button, isFavorite) => {
    button.setAttribute("aria-pressed", String(isFavorite));
    // Kart üzerindeki simge-butonlar (yer imi SVG'si) metinle EZİLMEMELİ;
    // yalnızca erişilebilirlik etiketi güncellenir.
    if (button.classList.contains("favorite-toggle")) {
      button.setAttribute("aria-label", isFavorite ? "Favoriden çıkar" : "Favorilere ekle");
      return;
    }
    const label = button.querySelector("[data-favorite-label]");
    if (label) {
      label.textContent = isFavorite ? "Favoriden çıkar" : "Favori";
    } else {
      button.textContent = isFavorite ? "Favoriden çıkar" : "Favori";
    }
  };

  const updateFavoriteBadge = () => {
    const favorites = readFavorites();
    document.querySelectorAll("[data-favorite-count]").forEach((badge) => {
      badge.textContent = String(favorites.length);
      badge.hidden = favorites.length === 0;
    });
  };

  const updateFavoritePanels = () => {
    const hasFavorites = readFavorites().length > 0;
    document.querySelectorAll("[data-favorites-panel]").forEach((panel) => {
      panel.hidden = !hasFavorites;
    });
  };

  const bindFavoriteButtons = () => {
    const favorites = readFavorites();
    document.querySelectorAll("[data-favorite-toggle]").forEach((button) => {
      if (button.dataset.favoriteBound === "true") {
        return;
      }
      const callId = Number.parseInt(button.getAttribute("data-call-id") || "", 10);
      if (!Number.isInteger(callId)) {
        return;
      }
      button.dataset.favoriteBound = "true";
      setButtonState(button, favorites.includes(callId));
      button.addEventListener("click", () => {
        const currentFavorites = readFavorites();
        const nextFavorites = currentFavorites.includes(callId)
          ? currentFavorites.filter((item) => item !== callId)
          : [callId, ...currentFavorites];
        writeFavorites(nextFavorites);
        setButtonState(button, nextFavorites.includes(callId));
        updateFavoriteBadge();
        updateFavoritePanels();
        window.dispatchEvent(new CustomEvent("hiberota:favorites-changed"));
      });
    });
  };

  const renderFavoritePage = async () => {
    const root = document.querySelector("[data-favorite-list-root]");
    if (!root) {
      return;
    }
    const emptyState = document.querySelector("[data-favorite-empty]");
    const favorites = readFavorites();
    if (favorites.length === 0) {
      root.innerHTML = "";
      if (emptyState) {
        emptyState.hidden = false;
      }
      return;
    }

    const endpoint = new URL(root.getAttribute("data-resolve-url") || "/cagrilar/favoriler/coz/", window.location.origin);
    endpoint.searchParams.set("ids", favorites.join(","));
    const response = await fetch(endpoint, { headers: { Accept: "application/json" } });
    const payload = await response.json();
    writeFavorites(payload.calls.map((call) => call.id));
    if (emptyState) {
      emptyState.hidden = payload.calls.length > 0;
    }
    root.innerHTML = payload.calls.map(renderFavoriteCard).join("");
    updateFavoriteBadge();
  };

  const renderFavoriteCard = (call) => `
    <article class="call-card">
      <div class="d-flex flex-column gap-2">
        <div>
          <h2 class="h6 mb-1"><a href="${call.url}">${escapeHtml(call.title)}</a></h2>
          <p class="text-secondary small mb-0">${escapeHtml(call.institution)}</p>
        </div>
        <p class="text-secondary small mb-0">Son tarih: ${escapeHtml(call.deadline || "Belirtilmemiş")}</p>
        <button class="btn btn-outline-secondary btn-sm" type="button" data-favorite-toggle data-call-id="${call.id}">
          Favoriden çıkar
        </button>
      </div>
    </article>
  `;

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  document.addEventListener("DOMContentLoaded", () => {
    bindFavoriteButtons();
    updateFavoriteBadge();
    updateFavoritePanels();
    renderFavoritePage()
      .then(bindFavoriteButtons)
      .catch(() => {
        const emptyState = document.querySelector("[data-favorite-empty]");
        if (emptyState) {
          emptyState.hidden = false;
        }
      });
  });
})();
