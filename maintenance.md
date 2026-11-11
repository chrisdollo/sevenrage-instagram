# 7rage maintenance

Once [SETUP.md](SETUP.md) is done, the page runs itself. This file covers
the little that's left and how to change things.

---

## What runs automatically

| When | What | Where |
|---|---|---|
| ~8:00 AM and ~7:00 PM New York, daily | Picks the next unused line, renders the image or Reel, publishes it, records it in `state.json` | `.github/workflows/post.yml` |
| Mondays | If fewer than 40 unused tweets are left, Claude writes 50 new ones and opens a pull request | `.github/workflows/refill.yml` |
| Mondays | Renews the Instagram token (it would expire after 60 days) | `.github/workflows/token.yml` |

The weekly plan (which post type goes out in which slot) is in the README.
Half the Reels get generated background music (calm, hopeful or bouncy,
matched to the line's mood) and half are silent.

---

## The only regular job: approve new lines (about once every 5 weeks, 2 min)

When the library runs low, GitHub emails you about a pull request called
**"New 7rage lines: approve by merging"**.

1. Open it (the GitHub phone app works fine).
2. Read the lines in the description.
3. Don't like some? **Files changed → tweets.txt → ⋯ → Edit file**, delete or
   reword them, and commit to the same branch.
4. Tap **Merge pull request → Confirm**. The new lines join the rotation.

If you never merge it, nothing breaks: after the unused lines run out, old
ones come back around (each line waits at least 60 days before it can repeat).

**Quotes** aren't auto-written, because Claude could misattribute a quote. The
100 in `quotes.txt` last about 25 weeks, then recycle. To add more, ask
Claude in this folder ("find 50 more quotes for quotes.txt that match
voice.md") and push the change.

---

## Optional but recommended: engagement (10–15 min a day)

The automation posts; it can't (and shouldn't) talk to people. Tools that
auto-comment or auto-reply break Instagram's rules. If you want faster growth:

- Reply to comments on the newest post in the first hour (`/ig-reply` helps).
- Leave 5–10 real comments on bigger pages in the niche (`/ig-comment`).
- Reshare posts to your story.

## Monthly check (optional, 20 min)

Copy last month's Insights (reach, shares, saves, follows per post) and run
`/ig-audit` in Claude Code. If one category clearly wins, ask Claude to
change the plan in `autopost/content.py` to post more of it.

---

## If something breaks

GitHub emails you when a workflow fails. Open the **Actions** tab, click the
red run and read the last lines.

| What the log says | Fix |
|---|---|
| `Instagram API … 190` or "access token" / "expired" | The token died (for example, the renewer stopped working). Generate a new one (SETUP.md step 3) and update the `IG_TOKEN` secret |
| `Instagram API … 10` / permission errors | Re-do SETUP.md step 3 and make sure both permissions are approved |
| `Pages site not reachable` | Check Settings → Pages → Source is "GitHub Actions" |
| Refresh token job fails at `gh secret set` | The `SECRETS_PAT` expired. Make a new one (SETUP.md step 5) |
| Refill job: `ANTHROPIC_API_KEY` / credit errors | Add credit at console.anthropic.com or replace the key |
| Scheduled runs stopped completely | GitHub pauses schedules on repos with no activity for 60 days. The bot's commits normally prevent this; if it happens, Actions → workflow → **Enable** |

A missed slot is simply skipped. The next slot posts normally.

---

## Changing things

Ask Claude in this folder, or edit and push:

| To change | Where |
|---|---|
| Post times | `SLOT_TIMES` in `autopost/content.py` **and** the `cron` line in `.github/workflows/post.yml` |
| Weekly plan (Reels / quotes / carousels per slot) | `PLAN` in `autopost/content.py` |
| How many Reels get music | `MUSIC_SHARE` in `autopost/content.py` (0 = all silent, 1 = all with music) |
| Caption phrasings, hashtags | `CAPTIONS`, `SEARCH`, `TAGS` in `autopost/content.py` |
| Colors, fonts, layout | `autopost/render.py` |
| The voice Claude writes in | `voice.md` |
| Add your own lines | `tweets.txt`, under the right `== A/B/C ==` section, with the next free number |

To see how something looks before it goes live, run on the Mac:

```bash
./preview tweet 24 --reel --mood=hopeful
./preview quote 48
./preview slot 2026-11-19-pm
```

Output lands in `previews/`.

**Pause posting:** Actions → *Post to Instagram* → ⋯ → **Disable workflow**.
Enable it again the same way.
