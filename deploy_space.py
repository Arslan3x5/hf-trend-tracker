"""Publish the dashboard files to the Hugging Face Space in one commit.

Usage (PowerShell):
    $env:HF_TOKEN = "<write token>"
    python deploy_space.py
"""
import os
import sys

from huggingface_hub import CommitOperationAdd, HfApi

SPACE_ID = os.getenv("SPACE_ID", "arslan3x5/hf-trend-tracker")

# local path -> path inside the Space
FILES = {
    "app.py": "app.py",
    "trends.py": "trends.py",
    "requirements.txt": "requirements.txt",
    "space/README.md": "README.md",
}


def main():
    token = os.getenv("HF_TOKEN")
    if not token:
        sys.exit("Set HF_TOKEN to a Hugging Face write token first.")
    api = HfApi(token=token)
    try:
        api.create_repo(SPACE_ID, repo_type="space", space_sdk="gradio", exist_ok=True)
    except Exception as exc:
        print("note: create_repo skipped, assuming the Space already exists:", type(exc).__name__)
    operations = [
        CommitOperationAdd(path_in_repo=remote, path_or_fileobj=local)
        for local, remote in FILES.items()
    ]
    api.create_commit(
        repo_id=SPACE_ID,
        repo_type="space",
        operations=operations,
        commit_message="Deploy dashboard",
    )
    print(f"Done: https://huggingface.co/spaces/{SPACE_ID}")


if __name__ == "__main__":
    main()