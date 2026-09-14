# Sponsor-Aware Job Agent：Windows 本地解压、安装与使用教程

## 1. 你下载到的是什么

这是源码型本地应用，不是无需依赖的单文件 EXE。首次安装会在项目目录内建立独立 Python 环境 `.venv`，并通过网络下载 Python 依赖与 Chromium。之后个人配置、简历、数据库和浏览器登录状态均保存在本机。

发布包不包含你的真实简历、电话、邮箱、Cookie、API Key 或历史投递数据库。

## 2. 解压

1. 下载 ZIP。
2. 右键选择“全部解压”。
3. 建议解压到短路径，例如：

```text
D:\job-agent
```

不要放在 ZIP 内直接运行，也尽量避免 OneDrive 同步目录、过深路径和含特殊符号的目录。

## 3. 安装前准备

必须安装：

- Windows 10/11 64 位；
- Python 3.12 或更高版本；
- 可联网下载依赖；
- Chromium、Chrome 或 Edge（Playwright 默认会下载独立 Chromium）。

验证 Python：打开 PowerShell，执行：

```powershell
py -3.12 --version
```

看到 `Python 3.12.x` 或更高版本即可。

## 4. 一键安装

双击：

```text
scripts/windows/01_INSTALL_WINDOWS.bat
```

脚本会依次：

1. 检查 Python；
2. 创建 `.venv`；
3. 安装运行依赖；
4. 安装 Playwright Chromium；
5. 复制配置模板到 `config/local/`；
6. 初始化 `data/jobs.db`；
7. 执行系统检查和合成规则评估。

如果 Playwright Chromium 下载失败，可稍后在项目目录的 PowerShell 中执行：

```powershell
.\.venv\Scripts\Activate.ps1
python -m playwright install chromium
```

如果 PowerShell 不允许激活脚本，可执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

也可以完全不激活环境，直接调用 `.venv\Scripts\python.exe` 或 `.venv\Scripts\job-agent.exe`。

## 5. 配置个人信息

双击 `scripts/windows/06_OPEN_CONFIG_FOLDER.bat`，编辑 `config/local/` 下的文件。不要修改 `config/examples/`，否则升级时难以区分模板与个人数据。

### 5.1 profile.yaml

建议填写：

```yaml
workspace_id: default
candidate_id: default
full_name: Your English Name
first_name: Your
last_name: Name
email: your@email.com
phone: "+86 1xxxxxxxxxx"
location: Shanghai, China
linkedin: ""
github: ""
```

### 5.2 preferences.yaml

```yaml
regions: [UK, NL, DE, IE, HK]
role_tracks: [technical, technical_business]
```

### 5.3 visa_answers.yaml

香港高才通尚未获批时可保留：

```yaml
routes:
  HK:
    route_type: HK_TTPS_C
    application_status: likely_eligible
```

状态必须反映真实情况。尚未获批时，不得把 `currently authorised to work in Hong Kong` 回答为 Yes。

### 5.4 screening_answers.yaml

这是工作权、Sponsor、搬迁、notice period 和薪资等固定答案的唯一可信来源。缺失答案会留空等待人工填写，不会自动猜测。

示例：

```yaml
answers:
  HK:
    likely:
      currently_authorized: "No"
      requires_employer_sponsorship: "No; I plan to obtain work authorisation independently through the Top Talent Pass Scheme."
      relocation_willingness: "Yes"
      notice_period: "To be confirmed"
      salary_expectation: "Open to discussion"
```

不要为了通过筛选而填写不真实答案。

## 6. 导入并审核简历

支持 PDF、DOCX、TXT、MD。

最简单方式：把简历文件拖到 `scripts/windows/03_IMPORT_RESUME.bat` 上；也可以执行：

```powershell
.\.venv\Scripts\job-agent.exe resume import "D:\CV\CV_Eng.pdf"
```

导入只会创建“待审核会话”，不会立即把识别结果当成事实。随后：

1. 双击 `scripts/windows/02_START_UI.bat`；
2. 打开 `Resume Import`；
3. 对每条识别结果选择 Accept、Edit、Reject、Merge 或 Resolve Conflict；
4. 只有批准的事实才允许用于后续简历和申请材料。

## 7. 配置职位源 boards.yaml

本版本不抓 LinkedIn/Indeed，而是直接读取四类公开 ATS 职位接口。每家公司需要一条 board 配置。

```yaml
boards:
  - platform: greenhouse
    company_name: Example Company
    board_token: example-company
    region_hint: UK

  - platform: lever
    company_name: Another Company
    board_token: another-company
    region_hint: IE

  - platform: ashby
    company_name: Startup Name
    board_token: startup-name
    region_hint: NL

  - platform: smartrecruiters
    company_name: Global Company
    board_token: GlobalCompany
    region_hint: DE
```

如何识别 token：

- Greenhouse：职位页常见为 `boards.greenhouse.io/TOKEN` 或 `job-boards.greenhouse.io/TOKEN`；
- Lever：`jobs.lever.co/TOKEN`；
- Ashby：`jobs.ashbyhq.com/TOKEN`；
- SmartRecruiters：`jobs.smartrecruiters.com/TOKEN`。

先配置少量目标公司，确认可运行后再扩充。错误 token 会在连接器健康状态中显示失败。

## 8. 配置 Sponsor/官方名录

把官方名单转换为 UTF-8 JSON 或 CSV，放入：

```text
config/local/registries/
```

JSON结构示例见：

```text
config/examples/registries/registry_example.json
```

必填字段包括：

```text
registry_record_id, country, legal_name, registry_identifier,
status, source, ruleset_version/version
```

可选字段包括：

```text
canonical_domain, aliases, effective_date, retrieved_at, metadata
```

注意：

- 英国与荷兰主要依赖官方雇主名录；
- 德国不是传统 Sponsor 名单逻辑，主要判断岗位、学历与薪资路线；
- 爱尔兰需要区分 Critical Skills 与 General Employment Permit；
- 香港高才通属于候选人自带工作权，获批后 `no sponsorship` 不应自动淘汰岗位。

名录和门槛会变化，使用前应更新。模糊公司名匹配只会送人工审核，不会直接当作官方证据。

## 9. 扫描与审核岗位

双击：

```text
scripts/windows/04_RUN_DAILY_SCAN.bat
```

或执行：

```powershell
.\.venv\Scripts\job-agent.exe run-daily --board-config config\local\boards.yaml
```

处理顺序：

```text
抓取 → 标准化 → 去重 → 工作权判断 → 硬过滤 → 双轨评分 → 人工审核队列
```

然后启动 `scripts/windows/02_START_UI.bat`，在 `Job Review` 中查看：

- 工作权路线和证据；
- 是否存在硬失败；
- Technical / Technical-business 轨道；
- 总分、匹配项、缺口和待核实项；
- 是否生成申请材料。

## 10. 生成并批准材料

在 `Job Review` 点击 `Generate package`，或使用命令：

```powershell
.\.venv\Scripts\job-agent.exe generate --job-id JOB_ID --candidate default
```

需要求职信时：

```powershell
.\.venv\Scripts\job-agent.exe generate --job-id JOB_ID --candidate default --cover-letter
```

进入 `Application Package`：

1. 查看每句话引用的 fact ID 与原始事实；
2. 检查数字、技能、日期和成果状态；
3. 检查工作权、薪资和notice period；
4. 批准或拒绝材料。

批准后的文件保存在：

```text
artifacts/applications/<package_id>/resume.pdf
artifacts/applications/<package_id>/cover_letter.pdf
```

## 11. 半自动填表

只有材料批准后才能填表。命令格式：

```powershell
.\.venv\Scripts\job-agent.exe autofill --application-id APPLICATION_ID --keep-open
```

系统会：

- 打开申请页；
- 识别并填写支持字段；
- 高亮工作权、Sponsor、薪资、搬迁和notice period；
- 遇到不确定字段或风险条件时暂停；
- 停在最终提交之前。

你必须亲自检查并点击外部网页的最终 Submit。系统没有生产代码会自动点击最终提交。

以下情况必须人工处理：CAPTCHA、登录/邮箱验证、法律声明、平等机会信息、重复申请、职位关闭、字符超限和未知页面结构。

## 12. 日常使用顺序

```text
每周更新 boards 与官方名录
→ 运行每日扫描
→ 在 UI 审核高分岗位
→ 生成并核对材料
→ 半自动填表
→ 手动提交
→ 回到 UI 记录结果
```

## 13. 自动定时扫描

`scheduler_examples/register-windows-task.ps1` 提供 Windows 任务计划模板。定时任务只抓取、判断和评分，不生成材料、不打开浏览器、不提交申请。

建议先手动稳定运行一周，再启用计划任务。

## 14. 数据备份和删除

重要本地目录：

```text
config/local/                  个人配置
data/jobs.db                   SQLite数据库
artifacts/resume_sources/      导入的简历原件
artifacts/applications/        生成材料
browser_profiles/default/      ATS登录状态和Cookie
```

备份时关闭 UI 和浏览器，再复制 `config/local`、`data` 和 `artifacts`。浏览器Cookie不建议跨设备复制。

清空动态数据：

1. 关闭 UI 和浏览器；
2. 删除 `data/jobs.db`；
3. 执行 `alembic upgrade head`；
4. 重新导入并审核简历。

## 15. 故障排查

### 安装失败

确认网络、Python版本和磁盘路径，然后重新运行 `scripts/windows/01_INSTALL_WINDOWS.bat`。若依赖安装中断，可在 PowerShell 执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[all]"
```

### UI启动失败

```powershell
.\.venv\Scripts\job-agent.exe doctor
.\.venv\Scripts\job-agent-ui.exe
```

### 数据库错误

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

### Chromium找不到

先执行：

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

也可临时指定本机浏览器：

```powershell
.\.venv\Scripts\job-agent.exe autofill --application-id APPLICATION_ID --browser-executable "C:\Program Files\Google\Chrome\Application\chrome.exe" --keep-open
```

### 扫描返回0

优先检查：

- board token 是否正确；
- 公司是否仍使用对应ATS；
- 网络能否访问公开接口；
- `boards.yaml` 缩进是否正确；
- 该公司当前是否确实有公开职位。

## 16. 当前版本限制

- 需要手动维护目标公司列表和官方名录；
- 不支持 LinkedIn、Indeed 或 Workday 全自动抓取；
- 简历解析为启发式提取，必须人工审核；
- 基础每日评分候选人快照仍较简化，后续应改为从批准事实库和偏好配置动态生成；
- 多用户字段已预留，但当前为本地单用户；
- OpenAI API 为可选能力，基础筛选与固定材料流程无需填写 API Key；
- 这不是移民或法律建议工具，最终工作权判断仍需核验官方规则与雇主要求。
