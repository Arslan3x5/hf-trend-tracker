# HF Trend Tracker

Hugging Face shows what is trending **today**. This project keeps a **daily
history** of the trending lists, so you can see what is *rising*, not just what
is big.

- **Live dashboard:** https://huggingface.co/spaces/arslan3x5/hf-trend-tracker
- **Dataset (updated daily):** https://huggingface.co/datasets/arslan3x5/hf-trend-history

## What it does

- Takes a snapshot of the top 300 trending **models, datasets and Spaces** every day
- Publishes the history as an open dataset on the Hugging Face Hub
- Shows what is **rising fastest** (like gains), what **just entered** the trending
  lists, and how any single item moved over time
- Runs as an **MCP server**, so AI agents can ask "what is rising in text-to-video?"

## How it works

```
GitHub Actions (daily, 03:15 UTC)
        |  collect.py
        v
Hugging Face dataset: data/YYYY-MM-DD.csv
        |  read by
        v
Gradio dashboard (Space) + MCP server
```

The collector runs on GitHub Actions, not on the Space, so snapshots keep
coming even when the free Space is asleep. The history cannot be rebuilt
later, so it gets more valuable every day.

## Project layout

| File | Purpose |
| --- | --- |
| `collect.py` | Fetches the trending lists and uploads one CSV per day |
| `trends.py` | Pure-pandas analysis: rising items, new entrants, item history |
| `app.py` | Gradio dashboard that also serves MCP tools |
| `tests/` | Unit tests for the analysis code |
| `.github/workflows/daily.yml` | Scheduled daily snapshot |
| `deploy_space.py` | Publishes the dashboard files to the Hugging Face Space |

## Data format

One CSV per day, one row per item per list:

| Column | Meaning |
| --- | --- |
| `date` | Snapshot date (UTC) |
| `kind` | `model`, `dataset` or `space` |
| `rank` | Position in the trending list (1 = top) |
| `id` | Repo id, e.g. `org/name` |
| `task` | Pipeline tag (models), task category (datasets) or SDK (Spaces) |
| `likes`, `downloads` | Counts at snapshot time (downloads is a rolling 30-day figure) |
| `trending_score` | Hugging Face's own trending score |
| `created_at` | Repo creation time |

## Use it from an AI agent (MCP)

The Space exposes three tools: `rising_models`, `new_in_trending` and
`history_of`. For clients that accept a remote MCP server by URL:

```json
{
  "mcpServers": {
    "hf-trend-tracker": {
      "url": "https://arslan3x5-hf-trend-tracker.hf.space/gradio_api/mcp/"
    }
  }
}
```

## Run locally

```
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:7860.

## Tests

```
pip install pytest
python -m pytest
```

## Roadmap

- Trend charts per task category
- Weekly summary post generated from the data
- Downloads growth once enough history exists

## License

MIT