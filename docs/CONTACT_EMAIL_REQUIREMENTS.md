# Admin and Security Contact Email Requirements

Status: waiting for real contact addresses

Date: 2026-06-25

This document defines the contact email contract for admin operations and responsible security disclosure. It does not assign real mailbox addresses.

## Required Environment Variables

```text
ADMIN_CONTACT_EMAIL=admin@example.invalid
SECURITY_CONTACT_EMAIL=security@example.invalid
SUPPORT_CONTACT_EMAIL=support@example.invalid
SECURITY_TXT_CONTACT=mailto:security@example.invalid
```

Rules:

- Placeholder `example.invalid` values must not be used in production.
- `ADMIN_CONTACT_EMAIL` is for operational/admin notifications.
- `SECURITY_CONTACT_EMAIL` is for responsible vulnerability reports and security notices.
- `SUPPORT_CONTACT_EMAIL` is for public support/contact routing when needed.
- `SECURITY_TXT_CONTACT` is the contact value planned for `.well-known/security.txt`.
- Public pages must not expose private staff identities, personal addresses, server details, or internal escalation paths.
- Inbound mailboxes must have owner access, backup ownership, MFA, and retention/triage expectations before launch.

## Completion Criteria

The related Phase 0 task can be marked complete only after:

- Real domain-based addresses are chosen.
- Mailbox ownership and MFA are confirmed.
- Values are placed in environment/secret management, not committed.
- The public security policy and future `security.txt` use the approved security contact.

## Current State

The repository is prepared with placeholder variables, but real admin/security notification addresses have not been provided. Therefore the related Phase 0 task is not marked complete.
