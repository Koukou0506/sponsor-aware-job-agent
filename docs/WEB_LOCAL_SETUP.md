# Local Web Setup

The product UI is local-first for real applications.

## Requirements

- Python 3.12+
- Node.js 20+ / npm
- local config under `config/local/` for real use

## Install

```bash
python -m pip install -e '.[all,dev]'
cd apps/web && npm install && cd ../..
```

## Run

macOS/Linux:
```bash
bash scripts/dev-local.sh
```

Windows PowerShell:
```powershell
./scripts/dev-local.ps1
```

Both launchers bind to loopback only:
- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:3000`

`APP_MODE=local` is explicit. Streamlit remains available separately as the admin/debug console.
