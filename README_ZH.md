# Sponsor-Aware Job Agent

一个面向国际求职者的本地优先、签证感知型职位发现与半自动投递系统。

[English README](README.md) · [架构](docs/ARCHITECTURE.md) · [设计决策](docs/DESIGN_DECISIONS.md) · [演示流程](docs/DEMO.md)

## 核心问题

传统自动投递工具通常先做关键词匹配，再填表；但对于需要工作许可或签证路径的候选人，真正的硬约束往往是：公司是否具备对应资质、岗位/薪资/合同是否满足路线要求，或者候选人是否已有独立工作权。

这个项目因此把 **Work Authorisation Fit 放在 Skill Fit 之前**。

## MVP能力

- Greenhouse / Lever / Ashby / SmartRecruiters 职位接入；
- 英国、荷兰、德国、爱尔兰、香港五地区工作权规则；
- Technical 与 Technical-business 双岗位轨道；
- 简历导入、事实拆分、人工批准与来源追溯；
- 岗位级材料生成和固定筛选题；
- Playwright 半自动填表；
- 最终提交必须由用户人工完成；
- SQLite + YAML 的本地数据与配置体系。

## 关键设计

```text
职位抓取
→ 去重与标准化
→ 工作权/签证判断
→ 岗位轨道分类与评分
→ 人工审核
→ 基于已验证事实生成材料
→ 人工批准
→ 自动填表
→ 人工最终提交
→ 投递追踪
```

香港候选人自带工作权路线与英国/荷兰等雇主担保路线使用不同逻辑，避免把所有国家压缩成一个简单的 `needs_sponsorship` 字段。

## 快速开始

推荐先看英文 README 的完整安装步骤。Windows 用户可同时参考：

- `docs/guides/windows-local-setup-zh.md`
- `scripts/windows/`

公开版包含一组可运行的 smoke tests：

```bash
pytest tests/public -q
python -m compileall -q src
job-agent evaluate-golden tests/golden/jobs/synthetic
```

> 本仓库是作品集/MVP，不提供移民或法律意见；正式使用时必须更新官方 Sponsor 名录、签证规则与薪资门槛。
