# Sponsor-Aware Job Agent

面向需要签证/工作权判断的国际求职者的本地优先求职 Agent。系统先判断岗位是否值得投，再进行通用技能匹配，而不是单纯追求海投数量。

## 两种运行模式

- **Demo Mode**：公开展示用，只使用合成岗位与合成候选人数据，不读取真实简历、SQLite、Cookie 或浏览器配置。
- **Local Mode**：实际求职用，可接入真实 ATS、简历事实库、工作权判断、申请材料、Tracker 和受控 Playwright 自动填表。

**最终 Submit 永远由用户手动点击。**

## 新 Web 架构

```text
Next.js
  -> FastAPI /api/v1
  -> Application Services
  -> Immigration / Matcher / Materials / Storage / Autofill
```

浏览器不独立实现签证、评分、事实校验或状态机规则。

## 页面

- Dashboard
- Discover Jobs
- Job Detail / Review
- Application Workspace
- Applications Table / Kanban
- Resume & Facts
- Immigration Evidence
- Secret-safe Settings

## Codex Skills

仓库内置两套 Skill：

- `sponsor-job-agent-dev`：修改/扩展该仓库时使用。
- `sponsor-job-agent-ops`：扫描岗位、审核、生成材料、准备 Autofill 等实际操作时使用。

安装：

```bash
bash scripts/install-skills.sh
```

Windows：

```powershell
./scripts/install-skills.ps1
```

详见 `docs/CODEX_SKILLS.md`。

## Demo 启动

```bash
python -m pip install -e '.[all,dev]'
APP_MODE=demo PYTHONPATH=src python -m uvicorn job_agent.api.app:app --host 127.0.0.1 --port 8000
```

另开终端：

```bash
cd apps/web
npm install
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
```

真实本地模式见 `docs/WEB_LOCAL_SETUP.md`。
