# Public Demo Deployment

The public deployment is **Demo Mode only**.

```text
APP_MODE=demo
```

It contains deterministic synthetic jobs and candidate facts. It must not mount:

- `config/local/`
- `data/`
- `artifacts/`
- `browser_profiles/`
- `.env`

It does not launch Playwright or connect to live ATS sources.

## Docker convenience

```bash
docker compose up --build
```

The compose file binds both services to loopback for local demonstration. For a public platform, deploy the same Demo API image and Web image behind the platform's network boundary. Do not deploy Local Mode with real candidate state to a public host.
