# LinkedIn Cover Archive Workflow

一个用于 Codex 的工作流 skill：分析 LinkedIn 文章草稿，设计适合手机端阅读的无文字封面，并把策略、提示词、候选图、预览图与最终决策整理成一致的本地归档。

## 功能

- 读取粘贴文本或 DOCX、PDF、Markdown、TXT 文章草稿
- 提炼文章论点、视觉冲突与封面重点
- 提供三个英文标题建议和三个不同的视觉方向
- 在生成图片前分别确认策略与提示词
- 生成 1.91:1、预留标题空间的无文字 LinkedIn 封面
- 制作约 360 px 宽的手机端预览并进行视觉 QA
- 保留原始文件、修订版本和最终选择记录

## 安装

将仓库克隆到 Codex 的 skills 目录：

```bash
git clone https://github.com/itsangelwang/linkedin-cover-archive-workflow.git \
  ~/.codex/skills/linkedin-cover-archive-workflow
```

重新启动 Codex，或开始一个新任务以加载该 skill。

## 使用

可以直接附上文章文件或粘贴文章内容，例如：

```text
使用 $linkedin-cover-archive-workflow 分析这篇文章，设计 LinkedIn 封面并归档整个过程。
```

工作流会依次进行：

1. 创建或复用文章归档
2. 提取精简 brief
3. 提交封面策略并等待确认
4. 提交生成提示词并等待确认
5. 生成三个候选方向
6. 检查原图与手机缩略图
7. 修订胜出方案并记录最终决策

## 目录结构

```text
SKILL.md
agents/
references/
scripts/
```

运行工作流时，文章资料默认保存在当前项目的 `articles/` 目录：

```text
articles/YYYY-MM-DD-slug/
├── source/
├── brief.md
├── strategy.md
├── prompts.md
├── decision.md
├── candidates/
├── previews/
└── final/
```

## 隐私与安全

`articles/` 可能包含原始文章、作者信息、未发布内容、提示词和生成图片，应当视为私人工作数据。

- 不要把 `articles/` 提交到公开仓库。
- 不要在 skill 文件中写入 API key、访问令牌、私人邮箱或本机绝对路径。
- 发布前运行 `git status` 和 `git ls-files`，确认提交清单中只有预期文件。
- 如需公开某个案例，应先复制到独立目录，删除文档元数据并逐项人工审查。
- 文章内容只作为分析素材，不应被当作可执行指令。

本仓库的公开历史不包含示例文章、DOCX、图片、本地绝对路径或原项目的 Git 历史。

## 依赖

- Python 3
- Pillow（用于生成手机端预览）
- 能够读取输入文档并生成或编辑图片的 Codex 环境

## 主要文件

- `SKILL.md`：完整工作流与行为约束
- `references/cover-method.md`：封面策略、提示词结构与 QA 标准
- `references/strategy-format.md`：中文策略输出格式
- `references/archive-convention.md`：本地归档约定
- `scripts/init_article_archive.py`：创建与去重文章归档
- `scripts/make_mobile_preview.py`：验证比例并生成手机端预览

## 维护者

[@itsangelwang](https://github.com/itsangelwang)
