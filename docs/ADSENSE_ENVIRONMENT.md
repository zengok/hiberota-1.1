# AdSense Environment Contract

Status: waiting for real Google AdSense identifiers

Date: 2026-06-25

This document defines how AdSense identifiers must be supplied. It does not include real publisher/client IDs and does not activate advertising.

## Required Environment Variables

```text
ADSENSE_ENABLED=false
ADSENSE_PUBLISHER_ID=
ADSENSE_CLIENT_ID=
```

Rules:

- `ADSENSE_ENABLED` must remain `false` until the real AdSense account is approved and staging checks pass.
- `ADSENSE_PUBLISHER_ID` is the Google publisher/account identifier used for `ads.txt` and related account ownership references.
- `ADSENSE_CLIENT_ID` is the public AdSense client identifier used by ad script configuration, typically shaped like `ca-pub-...`.
- Real values must be stored in environment/secret management, not committed to the repository.
- Empty or placeholder values must block ad script loading.
- Production ad activation also requires consent/CMP handling described in `docs/05_SEO_ANALYTICS_ADS.md`.

## Current State

The repository is prepared to receive the values safely through environment variables, but the actual publisher/client identifiers have not been provided. Therefore the related Phase 0 task is not marked complete.

## Activation Checklist

- Real publisher ID received from the AdSense account owner.
- Real client ID received from the AdSense account owner.
- Values added to staging secret storage.
- Staging verifies no ad script loads when consent is denied.
- Staging verifies ad script loads only when identity and consent are present.
- `ads.txt` is generated only after publisher ID is known.
- Production values are added through secure environment configuration.
