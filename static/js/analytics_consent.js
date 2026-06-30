(() => {
  const STORAGE_KEY = "hiberota:analytics-consent:v1";
  const CONSENT_GRANTED = "granted";
  const CONSENT_DENIED = "denied";
  const DENIED_CONSENT = {
    analytics_storage: "denied",
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
  };
  const ANALYTICS_GRANTED_CONSENT = {
    ...DENIED_CONSENT,
    analytics_storage: "granted",
  };

  const loadGa4 = (measurementId) => {
    if (!measurementId || document.querySelector("[data-ga4-script]")) {
      return;
    }
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };
    window.gtag("js", new Date());
    window.gtag("config", measurementId, {
      send_page_view: true,
    });

    const script = document.createElement("script");
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
    script.setAttribute("data-ga4-script", "");
    document.head.appendChild(script);
  };

  const loadAdsense = (clientId) => {
    if (!clientId || !clientId.startsWith("ca-pub-") || document.querySelector("[data-adsense-script]")) {
      return;
    }
    const script = document.createElement("script");
    script.async = true;
    script.crossOrigin = "anonymous";
    script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(clientId)}`;
    script.setAttribute("data-adsense-script", "");
    document.head.appendChild(script);
    document.querySelectorAll(".adsbygoogle").forEach(() => {
      window.adsbygoogle = window.adsbygoogle || [];
      window.adsbygoogle.push({});
    });
  };

  const updateConsent = (consent) => {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };
    window.gtag("consent", "update", consent);
  };

  const applyConsent = (measurementId, adsenseClientId, root, consent) => {
    if (consent === CONSENT_GRANTED) {
      updateConsent(ANALYTICS_GRANTED_CONSENT);
      if (root) {
        root.hidden = true;
      }
      loadGa4(measurementId);
      return;
    }
    if (consent === CONSENT_DENIED) {
      updateConsent(DENIED_CONSENT);
      if (root) {
        root.hidden = true;
      }
      return;
    }
    if (root) {
      root.hidden = false;
    }
  };

  const consentFromCmpDetail = (detail) => ({
    analytics_storage: detail.analytics_storage === "granted" ? "granted" : "denied",
    ad_storage: detail.ad_storage === "granted" ? "granted" : "denied",
    ad_user_data: detail.ad_user_data === "granted" ? "granted" : "denied",
    ad_personalization: detail.ad_personalization === "granted" ? "granted" : "denied",
  });

  const bindCmpBridge = (measurementId, adsenseClientId) => {
    window.addEventListener("hiberota:cmp-consent", (event) => {
      const consent = consentFromCmpDetail(event.detail || {});
      updateConsent(consent);
      if (consent.analytics_storage === "granted") {
        loadGa4(measurementId);
      }
      if (consent.ad_storage === "granted") {
        loadAdsense(adsenseClientId);
      }
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    const currentScript = document.querySelector('script[src$="/static/js/analytics_consent.js"]');
    const measurementId = currentScript?.getAttribute("data-ga4-measurement-id") || "";
    const adsenseClientId = currentScript?.getAttribute("data-adsense-client-id") || "";
    const cmpEnabled = currentScript?.getAttribute("data-cmp-enabled") === "true";
    const root = document.querySelector("[data-analytics-consent]");
    if (cmpEnabled) {
      bindCmpBridge(measurementId, adsenseClientId);
      return;
    }
    if (!root) {
      return;
    }
    applyConsent(measurementId, adsenseClientId, root, window.localStorage.getItem(STORAGE_KEY));
    root.querySelector("[data-analytics-accept]")?.addEventListener("click", () => {
      window.localStorage.setItem(STORAGE_KEY, CONSENT_GRANTED);
      applyConsent(measurementId, adsenseClientId, root, CONSENT_GRANTED);
    });
    root.querySelector("[data-analytics-deny]")?.addEventListener("click", () => {
      window.localStorage.setItem(STORAGE_KEY, CONSENT_DENIED);
      applyConsent(measurementId, adsenseClientId, root, CONSENT_DENIED);
    });
  });
})();
