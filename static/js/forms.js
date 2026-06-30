(() => {
  const bindAutoSubmitControls = () => {
    document.querySelectorAll("[data-auto-submit]").forEach((control) => {
      if (control.dataset.autoSubmitBound === "true") {
        return;
      }
      control.dataset.autoSubmitBound = "true";
      control.addEventListener("change", () => {
        control.form?.submit();
      });
    });
  };

  document.addEventListener("DOMContentLoaded", bindAutoSubmitControls);
})();
