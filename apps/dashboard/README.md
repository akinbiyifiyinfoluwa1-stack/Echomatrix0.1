# EchoMatrix Dashboard

React + TypeScript control console for the simulation-only EchoMatrix brain runtime.

## Run locally

```bash
npm install
npm run dev
```

Set `VITE_BRAIN_API_URL` when the brain runtime is hosted separately.

The dashboard currently reads `/brain/status` and deliberately does not invent live telemetry that the backend does not expose yet.
