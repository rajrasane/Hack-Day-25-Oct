# Safe Migration

Safe Migration is a human-in-the-loop dependency-upgrade control plane. It
turns a repository's dependency manifest into a reviewable upgrade proposal:
the user sees the manifest diff, security context, and breaking-change
warnings before explicitly approving or rejecting the change.

The project was built for Hack Day around four integrations:

- **Gemma 4 + Google Search Grounding** for upgrade recommendations and live
  release/security research.
- **Temporal** for a durable workflow that pauses at the human-approval gate.
- **JarvisLabs** for hosted-model inference benchmarking.
- **Kepler by Rubixkube** as the assisted DevOps environment for verification.

## What the frontend does today

The Next.js review dashboard is complete and runnable. A user can:

1. Enter a GitHub repository URL, dependency-file path, and project type.
2. Start an analysis and follow the Parsing → AI analysis → Human review
   workflow state.
3. Compare the current and proposed manifests.
4. Approve or reject a migration through the Temporal signal endpoint.

Until the Flask service is connected, the Next API routes return demo data and
the review panel displays a representative Python dependency upgrade. The API
contract below is the handoff for replacing those mock responses with live
analysis.

## Tech stack

- Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS
- Python 3.12 / Flask backend (separate repository or folder)
- Temporal Python SDK for workflow orchestration
- Gemma 4 through the Google Gen AI SDK, with Search Grounding

## Run the frontend

Use Node.js 20. The project pins the tested version in `.nvmrc`.

```bash
nvm install
nvm use
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

There are no frontend environment variables needed for the current demo. To
validate a production build:

```bash
npm run build
```

## Backend handoff: Flask API contract

Keep credentials and provider calls in Flask/Temporal—never in the browser.
The cleanest integration is to retain the Next routes as a small backend-for-
frontend proxy and have them call Flask via a server-only `FLASK_API_URL`.
This avoids exposing backend URLs, API credentials, or permissive browser CORS
rules.

### Start a migration

`POST /api/migrations`

```json
{
  "repo_url": "https://github.com/acme/atlas-api",
  "config_path": "requirements.txt",
  "project_type": "Python"
}
```

Required response while the workflow starts:

```json
{
  "workflow_id": "migration-123",
  "status": "RUNNING"
}
```

Use `REVIEW_READY` when the full review payload is already available. The
backend must reject missing fields with a JSON `400` response. Validate that
`repo_url` is an allowed GitHub HTTPS URL before cloning or fetching it; this
prevents server-side request forgery. Validate `config_path` as a relative path
inside the checked-out repository—never use it directly as an arbitrary
filesystem path.

### Deliver the review result

The frontend needs the following data once Temporal reaches the approval gate.
It may be returned by `POST /api/migrations` when immediately ready, or by a
status endpoint such as `GET /api/migrations/:workflow_id`.

```json
{
  "workflow_id": "migration-123",
  "status": "REVIEW_READY",
  "config_path": "requirements.txt",
  "original_manifest": "Django==4.2.7\n...",
  "upgraded_manifest": "Django==5.0.6\n...",
  "changes_count": 6,
  "breaking_changes": [
    {
      "package": "Django",
      "from_version": "4.2.7",
      "to_version": "5.0.6",
      "summary": "django.conf.urls.url was removed.",
      "severity": "warning"
    }
  ],
  "security_advisories": [
    {
      "package": "cryptography",
      "severity": "high",
      "summary": "Upgrade resolves a known advisory.",
      "source_url": "https://..."
    }
  ],
  "confidence": 94
}
```

The backend should validate Gemma output against this schema before returning
it. Preserve `workflow_id` throughout the workflow, return machine-readable
status values, and return safe error messages without provider tokens, stack
traces, or repository contents.

### Approve or reject

`POST /api/temporal/signal`

```json
{
  "workflow_id": "migration-123",
  "action": "APPROVE"
}
```

`action` is exactly `APPROVE` or `REJECT`. Return:

```json
{
  "ok": true,
  "action": "APPROVE"
}
```

Flask should signal the matching Temporal workflow, enforce the two allowed
actions, and make repeated signals idempotent. Applying a patch must occur
only after the workflow records `APPROVE`; `REJECT` must never modify the
target repository.

## Suggested Flask responsibilities

1. Clone/fetch the approved GitHub repository in an isolated workspace.
2. Parse the declared manifest without executing project code.
3. Call Gemma with a strict JSON schema; ground claims in release notes and
   advisories.
4. Start and track the Temporal workflow; expose its status/result to the
   Next frontend.
5. Send the approval signal and, only after approval, create the patch/branch
   and run verification commands.
6. Store `GEMINI_API_KEY`, Temporal credentials, and any JarvisLabs token in
   backend environment variables or a secrets manager. Do not return them to
   Next.js or commit them.

## Project layout

```text
app/
  page.tsx                     Review dashboard
  lib/migration-client.ts      Browser API client and TypeScript contract
  api/migrations/route.ts      Current migration-route mock / future Flask proxy
  api/temporal/signal/route.ts Current Temporal-signal mock / future Flask proxy
Context.md                     Hack Day brief and team responsibilities
```

## Demo flow

1. Submit the prefilled Atlas API Python example.
2. Show the workflow moving into Human review.
3. Point out the Django breaking-change warning and security grounding card.
4. Approve or reject; explain that Temporal resumes only after that explicit
   decision.
