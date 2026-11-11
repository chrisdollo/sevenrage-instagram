"""Write new 7rage lines with Claude when the library runs low. They land in a pull request,
so nothing new is posted until it's approved (merged).

  python autopost/refill.py           only acts if fewer than THRESHOLD unused tweets are left
  python autopost/refill.py --force   write a batch anyway

Needs ANTHROPIC_API_KEY. Writes tweets.txt in place plus .refill.md (the PR description).
"""
import json
import os
import re
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
THRESHOLD = 80  # about two weeks of posting at 6 a day
COUNTS = {"A": 16, "B": 10, "C": 14, "D": 16}
NAMES = {"A": "going through it (relatable, never hopeless)", "B": "get back up (quiet motivation)",
         "C": "laugh at it (humor and flex)",
         "D": "up early (posted at 5 AM: get up and go to work energy, no 'rise and grind' cliches)"}


def output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    for k, v in kv.items():
        print(f"{k}={v}")
        if path:
            with open(path, "a") as f:
                f.write(f"{k}={v}\n")


def unused_count(tweet_numbers):
    state = ROOT / "state.json"
    used = json.loads(state.read_text())["used"]["tweet"] if state.exists() else {}
    return sum(1 for n in tweet_numbers if str(n) not in used)


def ask_claude(voice, existing):
    schema = {
        "type": "object",
        "properties": {c: {"type": "array", "items": {"type": "string"}} for c in COUNTS},
        "required": list(COUNTS),
        "additionalProperties": False,
    }
    wanted = "\n".join(f"- {c} ({NAMES[c]}): {n} lines" for c, n in COUNTS.items())
    prompt = f"""You write the posts for @sevenrage7, an Instagram page that posts one line at a time as a
tweet-style image. Here is the page's voice and philosophy:

<voice>
{voice}
</voice>

Every line already in the library (don't repeat these or write close variations of them):

<existing>
{existing}
</existing>

Write new original lines:
{wanted}

Each line: one or two short sentences, usually under 20 words, sentence case (capital first letter and capital
"I"), spoken grammar is fine, the punch at the end. Even the "going through it" lines must not sound defeated
or hopeless: relatable, but the person is still standing. Write like a real person texting a friend, not a motivational poster. No em dashes,
no hashtags, no emoji, no slurs, nothing that puts down women or any group. Don't quote or paraphrase
famous people or songs. Every line should be something a 17-30 year old would send to a friend with
"this is you"."""

    client = anthropic.Anthropic()
    resp = client.beta.messages.create(
        model="claude-opus-5-5",
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}],
    )
    if resp.stop_reason == "refusal":
        sys.exit("Claude declined the request; no lines written.")
    if resp.stop_reason == "max_tokens":
        sys.exit("Response was cut off; no lines written.")
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


def clean(line):
    line = re.sub(r"\s*[—–]\s*", ", ", line.strip().strip('"'))
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r"\bi\b", "I", line[:1].upper() + line[1:])
    return line if 3 < len(line) <= 160 else None


def main():
    path = ROOT / "tweets.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    numbered = [(i, int(m.group(1)), m.group(2)) for i, l in enumerate(lines)
                if (m := re.match(r"^(\d+)\. (.+)$", l))]
    if unused_count([n for _, n, _ in numbered]) >= THRESHOLD and "--force" not in sys.argv:
        print("library is fine, nothing to do")
        return output(needed="false")

    voice = (ROOT / "voice.md").read_text(encoding="utf-8")
    seen = {t.lower() for _, _, t in numbered}
    new = ask_claude(voice, "\n".join(t for _, _, t in numbered))

    next_n = max(n for _, n, _ in numbered) + 1
    body = ["New lines written by Claude for the 7rage library.", "",
            "**Merge this pull request to approve them.** Nothing here gets posted until it's merged.",
            "To drop or change a line, edit `tweets.txt` in this PR first (Files changed → … → Edit file).",
            ""]
    for cat in COUNTS:
        header = next(i for i, l in enumerate(lines) if l.startswith(f"== {cat}."))
        end = header + 1
        while end < len(lines) and not lines[end].startswith("== ") and not lines[end].startswith("# "):
            end += 1
        while end > header + 1 and not lines[end - 1].strip():
            end -= 1
        added = []
        for raw in new.get(cat, []):
            t = clean(raw)
            if t and t.lower() not in seen:
                seen.add(t.lower())
                added.append(f"{next_n}. {t}")
                next_n += 1
        lines[end:end] = added
        body += [f"### {cat}. {NAMES[cat]} ({len(added)})", ""] + [f"- {a}" for a in added] + [""]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / ".refill.md").write_text("\n".join(body), encoding="utf-8")
    output(needed="true")


if __name__ == "__main__":
    main()
