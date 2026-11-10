"""Pure-pandas helpers: no network, easy to test."""
import pandas as pd

COLUMNS = ["id", "task", "likes", "likes_gain", "rank_now", "rank_change", "status"]


def _pick_dates(d, days):
    dates = sorted(d["date"].unique())
    if len(dates) < 2:
        return None, None
    latest = dates[-1]
    cutoff = pd.to_datetime(latest) - pd.Timedelta(days=days)
    older = [x for x in dates if pd.to_datetime(x) <= cutoff]
    base = older[-1] if older else dates[0]
    return base, latest


def rising(df, kind="model", days=7, task="all", top=20):
    """Items whose likes grew the most between the base and latest snapshot."""
    d = df[df["kind"] == kind]
    base, latest = _pick_dates(d, days)
    if base is None or base == latest:
        return pd.DataFrame(columns=COLUMNS)
    now = d[d["date"] == latest].set_index("id")
    then = d[d["date"] == base].set_index("id")
    out = now.join(then[["likes", "rank"]], rsuffix="_then")
    out["likes_gain"] = out["likes"] - out["likes_then"]
    out["rank_change"] = out["rank_then"] - out["rank"]  # positive = climbed
    out["status"] = out["likes_then"].isna().map({True: "new in list", False: ""})
    out = out.reset_index().rename(columns={"rank": "rank_now"})
    if task and task != "all":
        out = out[out["task"] == task]
    out = out.sort_values("likes_gain", ascending=False, na_position="last")
    return out[COLUMNS].head(int(top)).reset_index(drop=True)


def new_entrants(df, kind="model", days=7, top=20):
    """Items in the latest top list that were not in the base snapshot."""
    d = df[df["kind"] == kind]
    base, latest = _pick_dates(d, days)
    if base is None or base == latest:
        return pd.DataFrame(columns=["id", "task", "likes", "rank"])
    now = d[d["date"] == latest]
    old_ids = set(d[d["date"] == base]["id"])
    out = now[~now["id"].isin(old_ids)].sort_values("rank")
    return out[["id", "task", "likes", "rank"]].head(int(top)).reset_index(drop=True)


def item_history(df, item_id):
    d = df[df["id"] == item_id].sort_values("date")
    return d[["date", "likes", "downloads", "rank"]].reset_index(drop=True)


def tasks(df, kind="model"):
    return ["all"] + sorted(df[df["kind"] == kind]["task"].dropna().unique().tolist())