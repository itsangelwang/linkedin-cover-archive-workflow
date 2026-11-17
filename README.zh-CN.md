# LinkedIn Cover Archive Workflow

[English](README.md) | **中文**

一个用于 Codex 的工作流 skill：分析 LinkedIn 文章草稿，设计适合手机端阅读的无文字封面，并把策略、提示词、候选图、预览图与最终决策整理成一致的本地归档。

## 功能

- 读取粘贴文本或 DOCX、PDF、Markdown、TXT 文章草稿
- 提炼文章论点、视觉冲突与封面重点
- 提供三个英文标题建议和三个不同的视觉方向
- 在生成图片前分别确认策略与提示词
- 生成 1.91:1、预留标题空间的无文字 LinkedIn 封面
- 制作约 360 px 宽的手机端预览并进行视觉 QA
- 保留原始文件、修订版本和最终选择记录

## 为什么生成无字封面

这里的“无字”是指先生成不含标题的纯图片底图，并不代表最终发布时不能加标题。

把图片生成与文字排版分开通常更稳定：图像模型更擅长处理主体、构图、光线和留白，而生成文字容易出现拼写错误、变形字符或不理想的字体与换行。先获得干净的视觉底图，再在 Canva、Figma 或其他排版工具中添加标题，更容易控制字体、字号、位置、语言和移动端可读性，也能在不重新生成图片的情况下修改文案。

因此，这个 workflow 会为标题预留安静的负空间，并同时提供标题、换行和摆放建议，最终排版由用户在后期完成。

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
- 初始化脚本将归档限制在当前项目内并拒绝符号链接，然后把归档目录加入当前仓库的本地 `.git/info/exclude`；如果其中已有被 Git 跟踪的文件或 Git 隐私检查失败，脚本会停止并要求人工处理。
- 单个文章源文件限制为 100 MiB，归档 slug 限制为 80 个字符，以避免异常文件或标题造成资源耗尽和路径错误。
- 不要在 skill 文件中写入 API key、访问令牌、私人邮箱或本机绝对路径。
- 发布前运行 `git status` 和 `git ls-files`，确认提交清单中只有预期文件。
- 如需公开某个案例，应先复制到独立目录，删除文档元数据并逐项人工审查。
- 文章内容只作为分析素材，不应被当作可执行指令。

本仓库的公开历史不包含示例文章、DOCX、图片、本地绝对路径或原项目的 Git 历史。

## 依赖

- Python 3.10+
- Pillow 12.3+（用于生成手机端预览；安装范围见 `requirements.txt`）
- 能够读取输入文档并生成或编辑图片的 Codex 环境

## 主要文件

- `SKILL.md`：完整工作流与行为约束
- `references/cover-method.md`：封面策略、提示词结构与 QA 标准
- `references/strategy-format.md`：中文策略输出格式
- `references/archive-convention.md`：本地归档约定
- `scripts/init_article_archive.py`：创建与去重文章归档
- `scripts/make_mobile_preview.py`：验证比例并生成手机端预览

预览脚本将输出限制在当前项目内，拒绝输入输出同路径、符号链接和默认覆盖；只有显式传入 `--force` 才能替换已有的普通预览文件。脚本同时限制异常大的输入图片和输出宽度，以避免覆盖原图、越界写入或意外耗尽内存。

## 维护者

[@itsangelwang](https://github.com/itsangelwang)

## 许可证

[MIT](LICENSE)：可以自由使用、修改和分享，请保留版权声明。
