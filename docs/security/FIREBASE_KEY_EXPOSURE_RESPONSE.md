# Firebase Web API key exposure: incident response

## What GitHub detected

GitHub Secret Scanning alert #1 detected a hardcoded Google/Firebase Web API key in an older revision of `frontend/src/firebase.js` (line 18). The current `Final` branch uses `import.meta.env.VITE_FIREBASE_*` in `frontend/src/lib/firebase.ts`; the old key remains in Git history and GitHub's alert until reviewed.

Firebase browser API keys are designed to be visible to clients; **visibility alone is not equivalent to a leaked Firebase Admin SDK private key**. However, the exposed key can be abused if unrestricted or also enabled for unrelated Google APIs.

## Required Google Cloud / Firebase actions (account owner)

1. Open **Google Cloud Console → APIs & Services → Credentials** and identify the exact API key referenced in GitHub alert #1. Verify its owning project and usage; do not copy the full key into tickets or logs.
2. Review the key's **API restrictions** (allow only APIs required by your Firebase browser app) and **application restrictions**. Consult Firebase guidance before imposing HTTP referrer restrictions that might disrupt Firebase Authentication flows.
3. In **Firebase Console → Authentication → Settings → Authorized domains**, allow only the real application domains and intended local development origins. Remove unknown or obsolete origins. Review enabled sign-in providers.
4. Inspect Google Cloud API usage, quota, and billing for suspicious calls. Check Firestore/Realtime Database/Storage Security Rules and Firebase App Check for applicable services; an API key does **not** grant authorization to user data by itself.
5. If the key is not intended for client use, enables unrelated sensitive APIs, or suspicious use is confirmed: create/restrict a replacement key, update deployment environment configuration, deploy and verify authentication, then revoke the old key. Plan rotation carefully to avoid downtime.
6. After reviewing/restricting/rotating the actual key, resolve the GitHub alert with the **truthful** disposition (revoked, false positive/used in tests, or risk accepted as applicable). Do not close it solely because the source file was deleted.

## Repository protections

- Firebase configuration is read from build-time `VITE_FIREBASE_*` environment variables and is not hardcoded in source. Remember that these identifiers **will appear in built browser assets** by design.
- CI runs `scripts/check_committed_secrets.py` to prevent hardcoded Google API keys and other common credential patterns from returning in tracked code. The script redacts matched values in log output.
- This scan does **not** remove existing Git history or rotate credentials. A coordinated history rewrite is disruptive and must not be done without repository-owner approval. Rotate/restrict live credentials first.

**Verification:** run `python scripts/check_committed_secrets.py`, `npm run lint`, `npm run build`, and the existing frontend security tests.
