"""Content library, weekly plan, captions and line picking for 7rage."""
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TZ = "America/New_York"
# slot id -> local time. "0000" is midnight at the start of that date.
SLOT_TIMES = {"0000": (0, 0), "0500": (5, 0), "1000": (10, 0), "1200": (12, 0),
              "1600": (16, 0), "1900": (19, 0)}

# kinds: tweet = Reel, quote = image post, dump = 5-slide carousel of tweets
# tweet categories: A going through it, B get back up, C laugh at it, D up early (5 AM energy)
DAILY = {
    "0000": ("tweet", "A"),   # late night, relatable
    "0500": ("tweet", "D"),   # get up and work
    "1000": ("quote", None),
    "1200": ("tweet", "C"),   # lunch break laugh
    "1600": ("quote", None),
    "1900": ("tweet", "B"),   # evening push
}
# weekday (0 = Mon) -> {slot: (kind, category)} overrides
CHANGES = {2: {"1600": ("dump", None)}, 5: {"1600": ("dump", None)}}
PLAN = {d: {**DAILY, **CHANGES.get(d, {})} for d in range(7)}
DUMP_SIZE = 5
MUSIC_SHARE = {"A": 0.5, "B": 0.5, "C": 0.5, "D": 1.0}  # share of Reels with generated music; rest silent
MOOD = {"A": "calm", "B": "hopeful", "C": "bounce", "D": "bounce"}
RECYCLE_AFTER_DAYS = 60

CAPTIONS = {
    "A": ["send this to someone who gets it", "tag the friend who's been quiet lately",
          "be honest, how many of you are here right now", "for everyone handling it quietly"],
    "B": ["save this for the day you need it", "send this to your boy who's going through it",
          "read it again tomorrow morning", "this one's for whoever needed it today"],
    "C": ["send this to the friend who's built the same", "be honest, this is you",
          "tag someone who needs to laugh at their life today",
          "if you laughed you're probably going through it too"],
    "D": ["you up? good. send this to whoever's still asleep", "save this for tomorrow's alarm",
          "tag the friend you're working early with", "this is your sign. get up"],
    "quote": ["read that twice.", "save this one.", "send this to someone who needs it today.",
              "some lines age well."],
    "dump": ["which one is you? comment the number", "swipe till one hits. send it to who it's about",
             "pick one for today"],
}
SEARCH = ["daily motivation and relatable quotes for young men going through it.",
          "relatable quotes and daily motivation, every day.",
          "motivation for the ones handling it quietly."]
TAGS = {
    "A": "#relatablequotes #relatable #deepthoughts #mentalhealthmatters",
    "B": "#dailymotivation #motivationformen #keepgoing #discipline",
    "D": "#morningmotivation #discipline #dailymotivation #motivationformen",
    "C": "#relatablememes #relatablequotes #funnyquotes #relatable",
    "quote": "#quotestoliveby #dailymotivation #wisdom #motivationalquotes",
    "dump": "#relatablequotes #dailymotivation #motivationformen #relatable",
}


def load_tweets():
    """{n: (category, text)} from tweets.txt; category comes from '== A. ... ==' headings."""
    out, cat = {}, None
    for line in (ROOT / "tweets.txt").read_text(encoding="utf-8").splitlines():
        h = re.match(r"^== ([A-Z])\.", line)
        if h:
            cat = h.group(1)
            continue
        m = re.match(r"^(\d+)\. (.+)$", line)
        if m and cat:
            text = m.group(2).strip()
            out[int(m.group(1))] = (cat, text[:1].upper() + text[1:])
    return out


def load_quotes():
    """{n: (text, source)} from quotes.txt."""
    out = {}
    for line in (ROOT / "quotes.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+) \| [✓~] \| (.+?) \| (.+)$", line)
        if m:
            out[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip())
    return out


def attribution(source):
    """'Hemingway, The Old Man and the Sea' -> ('HEMINGWAY', 'The Old Man and the Sea')."""
    s = source.replace("*", "")
    s = re.sub(r"\s*\((?!\d{4}\))[^)]*\)", "", s).strip()  # drop notes, keep years
    if s.lower().startswith("attributed to "):
        return s[14:].upper(), "attributed"
    if ", " in s:
        a, w = s.split(", ", 1)
        return a.upper(), w
    return s.upper(), None


def pick(pool, used, today, rng, count=1):
    """Pick unused numbers from pool. If not enough, recycle the longest-ago used ones
    (only those older than RECYCLE_AFTER_DAYS, unless nothing else is left)."""
    free = [n for n in pool if str(n) not in used]
    rng.shuffle(free)
    chosen = free[:count]
    if len(chosen) < count:
        old = sorted((n for n in pool if str(n) in used), key=lambda n: used[str(n)])
        ripe = [n for n in old if (today - _date(used[str(n)])).days >= RECYCLE_AFTER_DAYS]
        for n in ripe + old:
            if len(chosen) == count:
                break
            if n not in chosen:
                chosen.append(n)
    return chosen


def _date(s):
    import datetime as dt
    return dt.date.fromisoformat(s[:10])


def caption(key, rng):
    return f"{rng.choice(CAPTIONS[key])}\n\n{rng.choice(SEARCH)}\n\n{TAGS[key]}"
