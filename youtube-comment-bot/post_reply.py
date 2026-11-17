"""Step 2 of the bot: when you add the `approve` (or `reject`) label to an issue,
post the reply to YouTube (or just close the issue).

Runs from .github/workflows/yt-post-reply.yml
"""

from __future__ import annotations

from googleapiclient.errors import HttpError

from bot_common import (
    LABEL_APPROVE, LABEL_COMMENT, LABEL_POSTED, LABEL_REJECT, GitHub, env,
    extract_comment_id, extract_reply, youtube_client,
)

MAX_REPLY_CHARS = 10000  # YouTube comment limit


def main() -> None:
    number = int(env("ISSUE_NUMBER"))
    action = env("LABEL_NAME")
    gh = GitHub()
    issue = gh.get_issue(number)
    labels = {lbl["name"] for lbl in issue.get("labels", [])}

    if LABEL_COMMENT not in labels:
        print("Ye bot ka issue nahi hai, kuch nahi karna.")
        return
    if LABEL_POSTED in labels:
        gh.comment(number, "ℹ️ Is comment ka reply pehle hi post ho chuka hai.")
        gh.remove_label(number, action)
        return

    if action == LABEL_REJECT:
        gh.comment(number, "❌ Reject kiya gaya. YouTube par koi reply nahi gaya.")
        gh.close(number, "not_planned")
        return
    if action != LABEL_APPROVE:
        return

    thread_id = extract_comment_id(issue.get("body"))
    reply = extract_reply(issue.get("body"))
    if not thread_id or not reply:
        gh.comment(number, "⚠️ Reply text khaali hai ya issue ka format toot gaya. "
                           "`reply-start` aur `reply-end` ke beech ke box mein reply likhkar "
                           "dobara `approve` label lagaiye.")
        gh.remove_label(number, LABEL_APPROVE)
        return
    if len(reply) > MAX_REPLY_CHARS:
        gh.comment(number, f"⚠️ Reply bahut lamba hai ({len(reply)} characters). Chhota karke dobara approve karein.")
        gh.remove_label(number, LABEL_APPROVE)
        return

    try:
        result = youtube_client().comments().insert(
            part="snippet",
            body={"snippet": {"parentId": thread_id, "textOriginal": reply}},
        ).execute()
    except HttpError as e:
        gh.comment(number, f"⚠️ YouTube par post nahi ho paya:\n```\n{str(e)[:800]}\n```\n"
                           "Theek karke dobara `approve` label lagaiye.")
        gh.remove_label(number, LABEL_APPROVE)
        raise SystemExit(1)

    video_id = result["snippet"].get("videoId", "")
    link = f"https://www.youtube.com/watch?v={video_id}&lc={result['id']}" if video_id else ""
    gh.comment(number, f"✅ Reply YouTube par post ho gaya! {link}")
    gh.add_labels(number, [LABEL_POSTED])
    gh.remove_label(number, LABEL_APPROVE)
    gh.close(number, "completed")


if __name__ == "__main__":
    main()
