# 7rage (@sevenrage7)

Daily motivation and relatable feelings for young adults going through it.
One line, twice a day, that reads like a friend texting you at 1am, not a
poster on a wall.

**Fully automated:** GitHub Actions renders and publishes every post through
Instagram's official API. Nothing to do day to day.

- First time? → [SETUP.md](SETUP.md)
- Running it, fixing it, changing it → [maintenance.md](maintenance.md)

---

## Files

| File | What it is |
|---|---|
| `voice.md` | The voice and page philosophy. Claude writes new lines from it, and the Instagram skills read it too |
| `tweets.txt` | Original 7rage lines, numbered, in 3 sections: A going through it, B get back up, C laugh at it |
| `quotes.txt` | Borrowed quotes: `NUMBER \| ✓/~ \| quote \| source`. ✓ = sourced, ~ = attribution uncertain (shown as "attributed") |
| `state.json` | What's been posted and when (written by the bot, created after the first post) |
| `logo.png` | Profile photo, also used as the avatar on tweet posts |
| `autopost/` | The automation: `run.py` (scheduler + Instagram publishing), `render.py` (images and Reels), `music.py` (generated background music), `content.py` (plan, captions, picking), `refill.py` (new lines via Claude) |
| `.github/workflows/` | When things run: posting, refilling, token renewal |
| `preview` | Preview any post on the Mac before it goes live |
| `tweet-examples/` | Reference tweets the voice is based on (local only, not on GitHub) |

## The voice (short version)

Mostly lowercase, one line, usually under 20 words, with the punch at the
end. Spoken grammar is fine ("ain't", "i be", "lowkey"). Mild swearing is
fine; slurs never ("man" instead of the n-word). No "rise and grind" clichés.
The full version is in `voice.md`.

## Look: Bone & Ink

| Role | Color |
|---|---|
| Background | `#EFEAE0` bone |
| Text | `#141414` ink |
| Muted (handle, attribution) | `#7A7268` |
| Accent | `#B4462B` rust |

- **Tweet style:** original lines. Logo, `7rage`, `@sevenrage7`, then the line (Inter font).
- **Quote style:** borrowed quotes, always credited (Gelasio italic).
- Reels are 7 seconds, 1080×1920, with a slow zoom. Half get generated
  background music matched to the mood, half are silent.

## Weekly plan: 2 posts a day (8:00 AM and 7:00 PM New York)

| Day | 8:00 AM | 7:00 PM |
|---|---|---|
| Mon | Tweet Reel (going through it) | Quote image |
| Tue | Tweet Reel (get back up) | Tweet Reel (laugh at it) |
| Wed | Tweet Reel (going through it) | Tweet dump, 5-slide carousel |
| Thu | Quote image | Tweet Reel (laugh at it) |
| Fri | Tweet Reel (get back up) | Tweet Reel (going through it) |
| Sat | Quote image | Tweet dump, 5-slide carousel |
| Sun | Tweet Reel (get back up) | Quote image |

That's 8 Reels, 4 quotes and 2 carousels a week, using about 18 tweet lines
and 4 quotes. Lines never repeat until the library is used up; then the
oldest come back after at least 60 days.

## Growth notes

1. **Shares** are one of Instagram's strongest signals. The captions ask for
   them ("send this to your boy who's going through it").
2. **Reels** reach people who don't follow you yet. Automated Reels can't
   use Instagram's trending audio (the API doesn't allow it), so expect
   somewhat less reach than hand-posted Reels with trending sounds.
3. **Engagement isn't automated, on purpose.** Replying to comments and
   commenting on bigger pages is the biggest manual growth lever. See
   maintenance.md.
4. **Hashtags:** 4 per post, used as labels; the limit is 5.
5. **Never** buy followers, use follow-for-follow, or give your password to
   "auto-engagement" tools.

## Profile setup

| Field | Status |
|---|---|
| Professional / Creator account | ✓ done |
| Bio | ✓ done |
| Name field: `7rage \| Daily Motivation` | ⏳ locked by Instagram, retry in a few days |
| Profile photo: `logo.png` | ⏳ |
| Pin 3 posts | ⏳ after the first week (best quote, best tweet, best Reel) |
| Highlights | ⏳ optional |
