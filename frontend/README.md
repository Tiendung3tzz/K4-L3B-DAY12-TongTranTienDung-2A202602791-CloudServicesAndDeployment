# Day12 Agent Frontend

Static chat frontend for the Railway backend. The project has no build step,
so it can be deployed directly to Vercel.

## Run locally

From this directory, use any static server, for example:

```bash
python -m http.server 5500
```

The `/api/*` proxy is configured by `vercel.json` for Vercel deployments.
When serving locally without Vercel, call the Railway backend directly or use
a local reverse proxy.

## Deploy to Vercel

In Vercel, import the repository and set **Root Directory** to `frontend`.
Alternatively, from this directory:

```bash
vercel
vercel --prod
```

The API key is entered in the settings panel and stored only in the current
browser session. Do not put `AGENT_API_KEY` in frontend source code or Vercel
public environment variables.
