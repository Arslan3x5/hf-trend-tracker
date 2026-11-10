import pandas as pd

import trends


def make_df():
    rows = []

    def add(date, rank, id_, task, likes):
        rows.append(
            dict(
                date=date,
                kind="model",
                rank=rank,
                id=id_,
                task=task,
                likes=likes,
                downloads=likes * 100,
                trending_score=1,
                created_at=None,
            )
        )

    add("2026-11-01", 1, "a/old", "text-generation", 100)
    add("2026-11-01", 2, "b/mid", "text-to-video", 50)
    add("2026-11-08", 1, "b/mid", "text-to-video", 400)
    add("2026-11-08", 2, "a/old", "text-generation", 110)
    add("2026-11-08", 3, "c/new", "text-to-video", 30)
    return pd.DataFrame(rows)


def test_rising_orders_by_likes_gain():
    out = trends.rising(make_df(), "model", days=7)
    assert out.iloc[0]["id"] == "b/mid"
    assert out.iloc[0]["likes_gain"] == 350


def test_new_entrants():
    out = trends.new_entrants(make_df(), "model", days=7)
    assert out["id"].tolist() == ["c/new"]


def test_needs_two_snapshots():
    df = make_df()
    df = df[df["date"] == "2026-11-08"]
    assert trends.rising(df, "model", days=7).empty


def test_task_filter():
    out = trends.rising(make_df(), "model", days=7, task="text-generation")
    assert out["id"].tolist() == ["a/old"]


def test_item_history_is_sorted_by_date():
    out = trends.item_history(make_df(), "b/mid")
    assert out["date"].tolist() == ["2026-11-01", "2026-11-08"]