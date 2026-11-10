"""Daily snapshot of Hugging Face trending models, datasets and Spaces.

Run by GitHub Actions once a day. Writes data/<date>.csv and, when HF_TOKEN and
DATASET_REPO are set, uploads it to a public dataset repo on the Hub.
"""
import datetime as dt
import os
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi

TOP_N = int(os.getenv("TOP_N", "300"))
TOKEN = os.getenv("HF_TOKEN")
DATASET_REPO = os.getenv("DATASET_REPO")


def dataset_task(tags):
    for tag in tags or []:
        if tag.startswith("task_categories:"):
            return tag.split(":", 1)[1]
    return None


def snapshot(api, date):
    fetchers = {
        "model": lambda: api.list_models(sort="trending_score", limit=TOP_N),
        "dataset": lambda: api.list_datasets(sort="trending_score", limit=TOP_N),
        "space": lambda: api.list_spaces(sort="trending_score", limit=TOP_N),
    }
    rows = []
    for kind, fetch in fetchers.items():
        try:
            for rank, item in enumerate(fetch(), start=1):
                if kind == "model":
                    task = getattr(item, "pipeline_tag", None)
                elif kind == "dataset":
                    task = dataset_task(getattr(item, "tags", None))
                else:
                    task = getattr(item, "sdk", None)
                created = getattr(item, "created_at", None)
                rows.append(
                    {
                        "date": date,
                        "kind": kind,
                        "rank": rank,
                        "id": item.id,
                        "task": task or "other",
                        "likes": getattr(item, "likes", None),
                        "downloads": getattr(item, "downloads", None),
                        "trending_score": getattr(item, "trending_score", None),
                        "created_at": str(created) if created else None,
                    }
                )
        except Exception as exc:  # keep going if one kind fails
            print(f"warning: could not fetch {kind}: {exc}", file=sys.stderr)
    return pd.DataFrame(rows)


def main():
    date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    api = HfApi(token=TOKEN)
    df = snapshot(api, date)
    if df.empty:
        print("error: nothing fetched", file=sys.stderr)
        sys.exit(1)

    out = Path("data")
    out.mkdir(exist_ok=True)
    path = out / f"{date}.csv"
    df.to_csv(path, index=False)
    print(f"saved {len(df)} rows to {path}")

    if TOKEN and DATASET_REPO:
        api.create_repo(DATASET_REPO, repo_type="dataset", exist_ok=True, private=False)
        api.upload_file(
            path_or_fileobj=str(path),
            path_in_repo=f"data/{date}.csv",
            repo_id=DATASET_REPO,
            repo_type="dataset",
            commit_message=f"snapshot {date}",
        )
        print(f"uploaded to {DATASET_REPO}")
    else:
        print("HF_TOKEN or DATASET_REPO not set: skipped upload")


if __name__ == "__main__":
    main()