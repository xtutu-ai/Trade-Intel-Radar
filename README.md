# Trade-Intel-Radar

轻量级每日交易情报雷达。每天自动收集 Trump、Musk、机构观点、AI 算力主线相关信息，识别主题变化，映射到 A 股/美股观察清单，并通过邮件发送 HTML 日报。

第一版按低配云服务器设计：2 CPU / 2GB 内存即可运行。不需要 PostgreSQL、Redis、Celery、前端或 Kubernetes。

## 功能

- X API：抓取指定账号和关键词。
- RSS：抓取公开新闻源。
- 官方页面：白宫、USTR、BIS、SEC 等入口。
- 本地研报目录：把合法获得的 PDF/TXT/MD 放到 `data/reports/` 自动解析。
- 规则评分：按来源、关键词、互动量粗筛。
- 主题迁移检测：比较历史主题权重，发现 GPU -> CPU/Memory/Networking 这类变化。
- LLM 分析：支持 OpenRouter、DeepSeek、硅基流动和其他 OpenAI-compatible API。
- HTML 邮件：cron 定时发送。
- SQLite：本地持久化。

## 快速开始

```bash
git clone https://github.com/xtutu-ai/Trade-Intel-Radar.git
cd Trade-Intel-Radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填入 X API、LLM API 和 SMTP 邮箱授权码。

测试：

```bash
python scripts/test_llm.py
python scripts/test_mail.py
python scripts/test_x.py
python scripts/run_daily.py --no-mail
```

正式运行：

```bash
python scripts/run_daily.py
```

## cron

```cron
30 7 * * 1-5 cd /opt/Trade-Intel-Radar && /opt/Trade-Intel-Radar/.venv/bin/python scripts/run_daily.py >> logs/cron.log 2>&1
30 20 * * 1-5 cd /opt/Trade-Intel-Radar && /opt/Trade-Intel-Radar/.venv/bin/python scripts/run_daily.py >> logs/cron.log 2>&1
```

## 低配机器建议

默认限制采集和 LLM 输入量。如果 2GB 内存压力大，在 `.env` 中降低：

```env
MAX_TOTAL_ITEMS=120
LLM_MAX_INPUT_ITEMS=40
LLM_MAX_TOKENS=2000
```

## 说明

这是情报整理系统，不是自动交易系统。不会绕过付费墙，也不会破解研报平台。完整研报请放入你合法拥有的文件。
