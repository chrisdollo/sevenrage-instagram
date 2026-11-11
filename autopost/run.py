"""7rage autoposter.

  python autopost/run.py prepare          decide if a post is due now; if so render it into site/
  python autopost/run.py publish          publish the prepared post to Instagram (needs IG_TOKEN, PAGES_URL)
  python autopost/run.py preview tweet 24 render a line to previews/ (also: quote 48, slot 2026-11-16-am)
  python autopost/run.py status           what's been posted, what's left

Env for testing: NOW=2026-11-16T08:10 pretends it's that local time.
"""
import datetime as dt
import json
import os
import random
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content as C  # noqa: E402


class _LazyRender:
    """Import the renderer (Pillow, numpy, ffmpeg) only when drawing, so `publish` runs without them."""
    def __getattr__(self, name):
        import render
        return getattr(render, name)


R = _LazyRender()

STATE = C.ROOT / "state.json"
SITE = C.ROOT / "site"
JOB = C.ROOT / ".job.json"
WINDOW_HOURS = 3  # a slot can still go out this long after its time (GitHub cron can lag)
IG = os.environ.get("IG_API_BASE", "https://graph.instagram.com") + "/" + os.environ.get("IG_API_VERSION", "v24.0")


def now_local():
    tz = ZoneInfo(C.TZ)
    if os.environ.get("NOW"):
        return dt.datetime.fromisoformat(os.environ["NOW"]).replace(tzinfo=tz)
    return dt.datetime.now(tz)


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"used": {"tweet": {}, "quote": {}}, "posted": {}}


def save_state(s):
    STATE.write_text(json.dumps(s, indent=1, sort_keys=True) + "\n")


def output(**kv):
    """Pass values to later GitHub Actions steps."""
    path = os.environ.get("GITHUB_OUTPUT")
    for k, v in kv.items():
        print(f"{k}={v}")
        if path:
            with open(path, "a") as f:
                f.write(f"{k}={v}\n")


def due_slot(state, now):
    for slot in ("pm", "am"):
        h, m = C.SLOT_TIMES[slot]
        at = now.replace(hour=h, minute=m, second=0, microsecond=0)
        sid = f"{now.date().isoformat()}-{slot}"
        if at <= now < at + dt.timedelta(hours=WINDOW_HOURS) and sid not in state["posted"]:
            return sid, slot
    return None, None


def build(sid, slot, date, state, outdir, rng):
    """Render the post for a slot. Returns the job description (not yet marked as used)."""
    tweets, quotes = C.load_tweets(), C.load_quotes()
    kind, cat = C.PLAN[date.weekday()][slot]
    outdir.mkdir(parents=True, exist_ok=True)
    job = {"slot": sid, "kind": kind, "cat": cat, "files": [], "text": []}
    if kind == "tweet":
        (n,) = C.pick([k for k, (c, _) in tweets.items() if c == cat], state["used"]["tweet"], date, rng)
        mood = C.MOOD[cat] if rng.random() < C.MUSIC_SHARE else None
        R.reel(R.tweet(tweets[n][1]), outdir / f"{sid}.mp4", mood, rng)
        job.update(nums=[n], files=[f"{sid}.mp4"], text=[tweets[n][1]], music=mood or "silent",
                   caption=C.caption(cat, rng))
    elif kind == "quote":
        (n,) = C.pick(list(quotes), state["used"]["quote"], date, rng)
        R.quote(*quotes[n]).save(outdir / f"{sid}.png")
        job.update(nums=[n], files=[f"{sid}.png"], text=[f"{quotes[n][0]} ({quotes[n][1]})"],
                   caption=C.caption("quote", rng))
    else:
        nums = C.pick(list(tweets), state["used"]["tweet"], date, rng, C.DUMP_SIZE)
        for i, n in enumerate(nums, 1):
            R.tweet(tweets[n][1]).save(outdir / f"{sid}-{i}.png")
        job.update(nums=nums, files=[f"{sid}-{i}.png" for i in range(1, len(nums) + 1)],
                   text=[tweets[n][1] for n in nums], caption=C.caption("dump", rng))
    return job


# ---------- Instagram API (official Content Publishing API, Instagram Login) ----------

def ig(method, path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{IG}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Instagram API {method} {path}: {e.code} {e.read().decode()[:500]}") from None


def wait_ready(container, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        st = ig("GET", container, fields="status_code,status").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container} failed: {st}")
        time.sleep(float(os.environ.get("POLL", 10)))
    raise RuntimeError(f"container {container} not ready after {timeout}s")


def publish_job(job, base_url):
    me = ig("GET", "me", fields="user_id,username")
    uid = me.get("user_id") or me["id"]
    urls = [base_url.rstrip("/") + "/" + f for f in job["files"]]
    if job["kind"] == "tweet":
        c = ig("POST", f"{uid}/media", media_type="REELS", video_url=urls[0],
               caption=job["caption"], share_to_feed="true")["id"]
    elif job["kind"] == "quote":
        c = ig("POST", f"{uid}/media", image_url=urls[0], caption=job["caption"])["id"]
    else:
        kids = [ig("POST", f"{uid}/media", image_url=u, is_carousel_item="true")["id"] for u in urls]
        for k in kids:
            wait_ready(k)
        c = ig("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(kids),
               caption=job["caption"])["id"]
    wait_ready(c)
    return ig("POST", f"{uid}/media_publish", creation_id=c)["id"], me.get("username")


# ---------- commands ----------

def cmd_prepare():
    state, now = load_state(), now_local()
    sid, slot = due_slot(state, now)
    if not sid:
        print(f"{now:%a %Y-%m-%d %H:%M} {C.TZ}: nothing due")
        return output(due="false")
    shutil.rmtree(SITE, ignore_errors=True)
    job = build(sid, slot, now.date(), state, SITE, random.Random())
    (SITE / "index.html").write_text("<!doctype html><title>7rage</title>")
    JOB.write_text(json.dumps(job, indent=1))
    print(f"prepared {sid}: {job['kind']} {job['nums']} {job.get('music', '')}")
    output(due="true")


def cmd_publish():
    job = json.loads(JOB.read_text())
    if not os.environ.get("IG_TOKEN"):
        print("IG_TOKEN not set: dry run, would publish:\n" + json.dumps(job, indent=1))
        return
    media_id, user = publish_job(job, os.environ["PAGES_URL"])
    state = load_state()
    key = "quote" if job["kind"] == "quote" else "tweet"
    day = job["slot"][:10]
    for n in job["nums"]:
        state["used"][key][str(n)] = day
    state["posted"][job["slot"]] = {"kind": job["kind"], "nums": job["nums"], "media_id": media_id,
                                    "music": job.get("music")}
    save_state(state)
    print(f"published {job['slot']} to @{user}: media {media_id}")


def cmd_preview(args):
    out = C.ROOT / "previews"
    out.mkdir(exist_ok=True)
    rng = random.Random()
    if args[0] == "slot":
        date = dt.date.fromisoformat(args[1][:10])
        job = build(args[1], args[1][11:], date, load_state(), out, rng)
        (out / f"{args[1]}.json").write_text(json.dumps(job, indent=1))
        print(json.dumps(job, indent=1))
        return
    kind, ref = args[0], " ".join(args[1:])
    if kind == "tweet":
        text = C.load_tweets()[int(ref)][1] if ref.isdigit() else ref
        img, name = R.tweet(text), f"tweet-{ref if ref.isdigit() else 'custom'}"
        img.save(out / f"{name}.png")
        if "--reel" in sys.argv:
            mood = next((a.split("=")[1] for a in sys.argv if a.startswith("--mood=")), "calm")
            R.reel(img, out / f"{name}.mp4", None if mood == "silent" else mood, rng)
    else:
        q = C.load_quotes()[int(ref)]
        name = f"quote-{ref}"
        R.quote(*q).save(out / f"{name}.png")
    print(f"previews/{name}.png")


def cmd_status():
    s, t, q = load_state(), C.load_tweets(), C.load_quotes()
    print(f"posted: {len(s['posted'])} posts")
    print(f"unused: {sum(1 for n in t if str(n) not in s['used']['tweet'])}/{len(t)} tweets, "
          f"{sum(1 for n in q if str(n) not in s['used']['quote'])}/{len(q)} quotes")
    for sid in sorted(s["posted"])[-6:]:
        print(" ", sid, s["posted"][sid])


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    {"prepare": cmd_prepare, "publish": cmd_publish, "status": cmd_status}.get(
        a[0] if a else "", lambda: cmd_preview(a[1:]) if a and a[0] == "preview" else print(__doc__))()
