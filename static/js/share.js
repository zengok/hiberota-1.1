(() => {
  const bindShareButtons = () => {
    document.querySelectorAll("[data-share-url]").forEach((button) => {
      if (button.dataset.shareBound === "true") {
        return;
      }
      button.dataset.shareBound = "true";
      button.addEventListener("click", () => {
        const url = button.getAttribute("data-share-url") || window.location.href;
        const title = document.title || "HibeRota";
        shareUrl(url, title, button);
      });
    });
  };

  const shareUrl = async (url, title, button) => {
    try {
      if (navigator.share) {
        await navigator.share({ title, url });
        setShareStatus(button, "Paylaşım penceresi açıldı.");
        return;
      }
      await navigator.clipboard.writeText(url);
      setShareStatus(button, "Bağlantı kopyalandı.");
    } catch {
      setShareStatus(button, "Bağlantı kopyalanamadı.");
    }
  };

  const setShareStatus = (button, message) => {
    let status = button.nextElementSibling;
    if (!status || !status.hasAttribute("data-share-status")) {
      status = document.createElement("span");
      status.className = "visually-hidden";
      status.setAttribute("aria-live", "polite");
      status.setAttribute("data-share-status", "");
      button.insertAdjacentElement("afterend", status);
    }
    status.textContent = message;
  };

  document.addEventListener("DOMContentLoaded", bindShareButtons);
})();
