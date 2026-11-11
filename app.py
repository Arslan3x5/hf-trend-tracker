import os
import time

import gradio as gr
import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

import trends

import spaces


@spaces.GPU
def _gpu_stub():
    """No-op. ZeroGPU Spaces need one @spaces.GPU function at startup."""
    return True

DATASET_REPO = os.getenv("DATASET_REPO", "arslan3x5/hf-trend-history")
DAYS_LOADED = 60
CACHE_SECONDS = 3600

_cache = {"time": 0.0, "df": None}


def get_history() -> pd.DataFrame:
    if _cache["df"] is not None and time.time() - _cache["time"] < CACHE_SECONDS:
        return _cache["df"]
    try:
        files = sorted(
            f
            for f in HfApi().list_repo_files(DATASET_REPO, repo_type="dataset")
            if f.startswith("data/") and f.endswith(".csv")
        )[-DAYS_LOADED:]
        frames = [
            pd.read_csv(hf_hub_download(DATASET_REPO, f, repo_type="dataset"))
            for f in files
        ]
        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    except Exception as exc:
        raise gr.Error(f"Could not load history from {DATASET_REPO}: {exc}")
    if df.empty:
        raise gr.Error("No snapshots yet. The first daily run has not happened.")
    _cache.update(time=time.time(), df=df)
    return df


def rising_models(kind: str, days: int, task: str, top: int):
    """List the fastest-rising items on the Hugging Face Hub.

    Args:
        kind: What to rank: "model", "dataset" or "space".
        days: Compare today with this many days ago (1 to 30).
        task: Task filter such as "text-to-video", or "all".
        top: How many rows to return.
    """
    df = get_history()
    out = trends.rising(df, kind, int(days), task, int(top))
    if out.empty:
        raise gr.Error("Not enough history yet: need at least 2 daily snapshots.")
    return out


def new_in_trending(kind: str, days: int, top: int):
    """List items that newly entered the Hub trending list.

    Args:
        kind: "model", "dataset" or "space".
        days: Look back this many days.
        top: How many rows to return.
    """
    df = get_history()
    out = trends.new_entrants(df, kind, int(days), int(top))
    if out.empty:
        raise gr.Error("Not enough history yet, or nothing new.")
    return out


def history_of(item_id: str):
    """Daily likes, downloads and trending rank for one Hub item.

    Args:
        item_id: Repo id such as "org/name".
    """
    out = trends.item_history(get_history(), item_id.strip())
    if out.empty:
        raise gr.Error("That id was never in the tracked top list.")
    return out


with gr.Blocks(title="HF Trend Tracker") as demo:
    gr.Markdown(
        "# HF Trend Tracker\n"
        "Daily snapshots of the Hugging Face trending lists, so you can see what is "
        "**rising**, not just what is big. Data: "
        f"[{DATASET_REPO}](https://huggingface.co/datasets/{DATASET_REPO})."
    )
    with gr.Tab("Rising"):
        kind = gr.Radio(["model", "dataset", "space"], value="model", label="Type")
        days = gr.Slider(1, 30, value=7, step=1, label="Days back")
        task = gr.Textbox(value="all", label="Task filter (e.g. text-to-video, or all)")
        top = gr.Slider(5, 100, value=20, step=5, label="Rows")
        go = gr.Button("Show rising", variant="primary")
        table = gr.Dataframe()
        go.click(rising_models, [kind, days, task, top], table, api_name="rising_models")
    with gr.Tab("New in trending"):
        k2 = gr.Radio(["model", "dataset", "space"], value="model", label="Type")
        d2 = gr.Slider(1, 30, value=7, step=1, label="Days back")
        t2 = gr.Slider(5, 100, value=20, step=5, label="Rows")
        g2 = gr.Button("Show new entrants", variant="primary")
        table2 = gr.Dataframe()
        g2.click(new_in_trending, [k2, d2, t2], table2, api_name="new_in_trending")
    with gr.Tab("One item over time"):
        item = gr.Textbox(label="Repo id, e.g. org/name")
        g3 = gr.Button("Show history", variant="primary")
        plot = gr.LinePlot(x="date", y="likes", title="Likes over time")
        table3 = gr.Dataframe()

        def _both(item_id):
            out = history_of(item_id)
            return out, out

        g3.click(_both, item, [plot, table3], api_name="history_of")

if __name__ == "__main__":
    demo.launch(mcp_server=True)