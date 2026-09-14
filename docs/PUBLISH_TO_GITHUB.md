# Publish This Repository to GitHub

## GitHub Desktop

1. Extract the ZIP to a normal local folder, for example `D:\Projects\sponsor-aware-job-agent`.
2. Open GitHub Desktop and choose **File → Add local repository**.
3. If GitHub Desktop says the folder is not yet a repository, choose **create a repository here**.
4. Use repository name `sponsor-aware-job-agent` and make the first commit.
5. Choose **Publish repository**. Start as **Private** if you want one final review before making it public.
6. On GitHub, verify that `.env`, `config/local/`, `data/`, `artifacts/`, `browser_profiles/` and real resumes are absent.

## Command line

Create an empty GitHub repository first, then run from the extracted folder:

```powershell
git init
git add .
git status
git commit -m "Initial public portfolio release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sponsor-aware-job-agent.git
git push -u origin main
```

Before committing, `git status` must **not** show real resumes, `.env`, local candidate configuration, browser profiles or the SQLite database.

## Recommended repository description

> Sponsor-aware, local-first job discovery and semi-automated application agent with ATS integrations, five-region work-authorisation logic, fact-grounded resume tailoring and supervised Playwright autofill.

## Suggested GitHub topics

`python`, `job-search`, `automation`, `playwright`, `streamlit`, `sqlalchemy`, `ats`, `career-tools`, `llm`, `human-in-the-loop`
