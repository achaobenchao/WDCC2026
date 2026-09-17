# WDCC2026

检索素材文件。

This repository contains compact, project-local Agent Skills for a future batch
video-material search and Excel-indexing workflow. It does not include video
analysis results, model weights, or third-party source trees.

## Setup

Use a supported Python environment (Python 3.10 or newer is recommended):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install PaddlePaddle **before** `requirements.txt`, choosing the CPU or GPU build
for the current operating system and accelerator from the official
[PaddlePaddle installation guide](https://www.paddlepaddle.org.cn/install/quick).
Do not guess a CUDA build. On macOS, use the supported CPU instructions. Then run:

```bash
python -m pip install -r requirements.txt
```

FFmpeg and `ffprobe` are system executables, not Python packages. Install them
with the operating system package manager and verify both are on `PATH`:

```bash
ffmpeg -version
ffprobe -version
```

Models used by PaddleOCR and faster-whisper are intentionally not committed;
their packages download model data into a local cache when first used.

## Video Analysis Skills

- **FFmpeg** — reads video metadata, extracts audio, and captures frames at exact
  timestamps. See `skills/ffmpeg/SKILL.md`.
- **PaddleOCR** — recognizes Chinese and other text in selected keyframes. See
  `skills/paddleocr/SKILL.md`.
- **faster-whisper** — transcribes Chinese or auto-detected speech with segment
  timestamps. See `skills/transcription/SKILL.md`.
- **PySceneDetect** — detects shot boundaries and plans a small but sufficient
  set of representative frames. See `skills/video-scene-analysis/SKILL.md`.
- **openpyxl** — writes the final multi-sheet `视频素材检索结果.xlsx`. See
  `skills/xlsx/SKILL.md`.

The intended later workflow is: scan videos → probe metadata → detect scenes →
select keyframes → OCR/transcribe → fuse people, events, and timestamps → Excel.
This setup stage does not run that workflow.

## Project Architecture

```
NAS 原始视频（不进入 GitHub）
  → 视频分析与人工修订
  → 人工修订 Excel 总表
  → SQLite 本地索引
  → 命令行查询 / 后续导出与系统扩展
```

人工修订后的 Excel 是当前数据库初始化的权威来源。导入过程只读取
Excel，不会重新运行视频分析，也不会覆盖人工文本。

## Data Storage

- NAS 原始视频、关键帧、音频、模型缓存、日志和分析输出不上传 GitHub。
- 真实 SQLite 数据库默认保存在 `database/video_index.db`，由 `.gitignore`
  排除；仓库只保存 Schema 与程序。
- Excel 行保留 `来源表格`、`来源Sheet` 和批次信息，数据库也保留这些追溯字段。

## Database Setup

从项目根目录运行。首次导入会自动创建 SQLite 数据库和数据表；再次导入
同一总表使用 UPSERT，不会重复写入视频、人物关系、事件或关键词。

```bash
python scripts/import_excel_to_db.py \
  "/Volumes/公用文件夹/WDCC2026/视频文件检索目录beta版/视频文件检索总表_beta汇总版.xlsx"

python scripts/db_stats.py
python scripts/query_db.py person "张三"
python scripts/query_db.py event "签约"
python scripts/query_db.py keyword "采访"
python scripts/query_db.py file "会议"
python scripts/query_db.py video "某个视频文件名"
python scripts/query_db.py review
```

数据库 Schema 位于 `database/schema.sql`；数据库连接和时间解析等共享逻辑
位于 `database/db.py`。所有中文字段均以 UTF-8 文本保存。

## GitHub

仓库保存项目源码、Skills、Schema、导入/查询脚本、配置与文档。它不保存
NAS 原始视频、模型、缓存、真实数据库、Excel 成果或任何凭据。

## Upstream projects and licenses

| Component or reference | Upstream | License |
|---|---|---|
| FFmpeg | [FFmpeg](https://ffmpeg.org/) | LGPL 2.1+ by default; optional build components may make a binary GPL-covered |
| FFmpeg skill design reference | [n0an/ffmpeg-skill](https://github.com/n0an/ffmpeg-skill) | MIT |
| PaddleOCR and official text-recognition skill | [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Apache-2.0 |
| faster-whisper | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT |
| PySceneDetect | [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | BSD-3-Clause |
| OpenCV Python package | [opencv/opencv-python](https://github.com/opencv/opencv-python) | Apache-2.0 |
| openpyxl | [openpyxl/openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) | MIT |

The local skills are narrowly written operating instructions, not copies of
upstream repositories. The public `anthropics/skills` XLSX workflow was reviewed
as a design reference; its proprietary text is not included here.
