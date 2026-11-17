"""Shared helpers for the YouTube comment reply bot (YouTube API + GitHub Issues)."""

from __future__ import annotations

import os
import re
import sys

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

YT_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# Labels used on GitHub issues
LABEL_COMMENT = "yt-comment"   # every issue created by the bot
LABEL_APPROVE = "approve"      # you add this -> reply gets posted
LABEL_REJECT = "reject"        # you add this -> issue closed, nothing posted
LABEL_POSTED = "yt-posted"     # bot adds this after posting
LABEL_SKIPPED = "yt-skipped"   # bot adds this when Claude suggests not replying

LABELS = {
    LABEL_COMMENT: ("0e8a16", "YouTube comment draft (bot)"),
    LABEL_APPROVE: ("1d76db", "Isko lagao to reply YouTube par post hoga"),
    LABEL_REJECT: ("b60205", "Isko lagao to reply nahi jayega"),
    LABEL_POSTED: ("5319e7", "Reply YouTube par post ho gaya"),
    LABEL_SKIPPED: ("cccccc", "Bot ne reply na dene ka sujhav diya"),
}

ID_MARKER = re.compile(r"<!--\s*yt-comment-id:\s*([A-Za-z0-9_\-]+)\s*-->")
REPLY_BLOCK = re.compile(r"<!--\s*reply-start\s*-->(.*?)<!--\s*reply-end\s*-->", re.S)


def env(name: str, default: str | None = None, required: bool = True) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        sys.exit(f"ERROR: environment variable {name} set nahi hai (GitHub Secret check karein).")
    return value or ""


# ---------------------------------------------------------------- YouTube

def youtube_client():
    creds = Credentials(
        token=None,
        refresh_token=env("YT_REFRESH_TOKEN"),
        client_id=env("YT_CLIENT_ID"),
        client_secret=env("YT_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=YT_SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------- GitHub

class GitHub:
    def __init__(self) -> None:
        self.repo = env("GITHUB_REPOSITORY")
        self.api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {env('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _url(self, path: str) -> str:
        return f"{self.api}/repos/{self.repo}{path}"

    def request(self, method: str, path: str, **kwargs):
        resp = self.session.request(method, self._url(path), timeout=30, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(f"GitHub API {method} {path} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json() if resp.content else None

    def ensure_labels(self) -> None:
        existing = {lbl["name"] for lbl in self.request("GET", "/labels", params={"per_page": 100})}
        for name, (color, desc) in LABELS.items():
            if name not in existing:
                self.request("POST", "/labels", json={"name": name, "color": color, "description": desc})

    def bot_issues_since(self, since_iso: str) -> list[dict]:
        issues, page = [], 1
        while True:
            batch = self.request("GET", "/issues", params={
                "labels": LABEL_COMMENT, "state": "all", "since": since_iso,
                "per_page": 100, "page": page,
            })
            issues.extend(batch)
            if len(batch) < 100:
                return issues
            page += 1

    def create_issue(self, title: str, body: str, labels: list[str]) -> dict:
        return self.request("POST", "/issues", json={"title": title, "body": body, "labels": labels})

    def get_issue(self, number: int) -> dict:
        return self.request("GET", f"/issues/{number}")

    def comment(self, number: int, text: str) -> None:
        self.request("POST", f"/issues/{number}/comments", json={"body": text})

    def add_labels(self, number: int, labels: list[str]) -> None:
        self.request("POST", f"/issues/{number}/labels", json={"labels": labels})

    def remove_label(self, number: int, label: str) -> None:
        resp = self.session.delete(self._url(f"/issues/{number}/labels/{label}"), timeout=30)
        if resp.status_code not in (200, 404):
            raise RuntimeError(f"Label remove failed: {resp.status_code} {resp.text[:200]}")

    def close(self, number: int, reason: str = "completed") -> None:
        self.request("PATCH", f"/issues/{number}", json={"state": "closed", "state_reason": reason})


# ---------------------------------------------------------------- text helpers

def neutralize(text: str) -> str:
    """Make untrusted YouTube text safe to show in a GitHub issue:
    no accidental @mentions, no fake bot markers."""
    text = text.replace("<!--", "&lt;!--").replace("-->", "--&gt;")
    return re.sub(r"@(?=\w)", "@​", text)


def clean_reply(text: str) -> str:
    """Reply text that goes inside a ```text fence in the issue body."""
    return text.replace("```", "'''").replace("<!--", "").replace("-->", "").strip()


def extract_reply(body: str) -> str:
    """Pull the (possibly edited) reply out of an issue body."""
    match = REPLY_BLOCK.search(body or "")
    if not match:
        return ""
    lines = match.group(1).strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).replace("​", "").strip()


def extract_comment_id(body: str) -> str | None:
    match = ID_MARKER.search(body or "")
    return match.group(1) if match else None
