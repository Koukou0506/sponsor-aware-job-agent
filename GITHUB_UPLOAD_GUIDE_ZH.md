# GitHub 上传指南

这份 ZIP 已按公开作品集仓库整理。**请上传解压后的文件夹内容，不要把 ZIP 本身作为仓库唯一文件。**

## 方法一：GitHub Desktop（推荐）

1. 将 ZIP 解压，例如：`D:\Projects\sponsor-aware-job-agent`。
2. 在 GitHub 网站新建一个空仓库，建议名称：`sponsor-aware-job-agent`。
3. 创建仓库时先不要添加 README、`.gitignore` 或 License；本项目已经包含 README 和 `.gitignore`。
4. 打开 GitHub Desktop，选择 `File → Add local repository`。
5. 选择解压后的 `sponsor-aware-job-agent` 文件夹。
6. 如果提示该目录尚不是 Git repository，选择在此创建 repository。
7. 第一次提交建议写：`Initial public portfolio release`。
8. 点击 `Publish repository`。
9. 建议先设为 **Private**，在 GitHub 网页检查一次后再改成 Public。

## 方法二：命令行

先在 GitHub 新建空仓库，然后在解压目录打开 PowerShell：

```powershell
git init
git add .
git status
git commit -m "Initial public portfolio release"
git branch -M main
git remote add origin https://github.com/你的用户名/sponsor-aware-job-agent.git
git push -u origin main
```

## 上传前必须检查

执行：

```powershell
git status
```

不应出现：

```text
.env
config/local/
data/
artifacts/
browser_profiles/
真实简历 PDF/DOCX/TXT/MD
API Key
Cookie
```

本仓库的 `.gitignore` 已默认排除上述运行数据，并额外忽略 `user_files/resumes/` 中除占位说明以外的文件。

## 建议的 GitHub 仓库简介

> Sponsor-aware, local-first job discovery and semi-automated application agent with ATS integrations, five-region work-authorisation logic, fact-grounded resume tailoring and supervised Playwright autofill.

## 建议 Topics

```text
python
job-search
automation
playwright
streamlit
sqlalchemy
ats
career-tools
llm
human-in-the-loop
```

## 公开后建议检查

- README 首页 Mermaid 架构图是否正常渲染；
- GitHub Actions 中 `public-smoke` 是否变绿；
- `config/examples/` 中只有示例信息；
- Repository 中搜索自己的姓名、邮箱、手机号，应没有真实结果；
- `data/`、`artifacts/`、`browser_profiles/` 不应存在。
