# One-time setup (about 1 hour)

After this, @sevenrage7 posts six times a day by itself. You never have to touch
it again, except to approve new lines every week or two (one tap on GitHub).

You'll create 3 free accounts and paste 3 keys. Do the steps in order.

---

## 1. Put the project on GitHub (10 min)

1. Create a free account at **github.com** if you don't have one.
2. Click **+ → New repository**.
   - Name: `7rage`
   - Visibility: **Public**. This is required for free hosting of the images
     and unlimited free automation minutes. Anyone could see the line library
     and code, but nothing private is in it (your example screenshots stay
     off GitHub).
   - Don't add a README or anything else. Click **Create repository**.
3. In Terminal on your Mac:

   ```bash
   cd ~/Desktop/instagram
   git init -b main
   git add .
   git commit -m "7rage autoposter"
   git remote add origin https://github.com/YOUR-USERNAME/7rage.git
   git push -u origin main
   ```

   When it asks for a password, use a GitHub token, not your password. The
   easiest way is to install GitHub Desktop or run `brew install gh && gh auth login`
   first. (Or ask Claude to walk you through it.)

## 2. Turn on Pages and permissions in the repo (3 min)

In your repo on github.com:

1. **Settings → Pages** → under *Build and deployment*, set Source to
   **GitHub Actions**.
2. **Settings → Actions → General** → scroll to *Workflow permissions*:
   - select **Read and write permissions**
   - tick **Allow GitHub Actions to create and approve pull requests**
   - click **Save**

## 3. Get the Instagram key (20–30 min)

This uses Meta's official publishing API. Meta's screens change often, so the
button names below may be slightly different.

1. Make sure @sevenrage7 is a **Professional account** (Creator is fine). ✓ already done.
2. Go to **developers.facebook.com**, log in with Facebook (any account
   works), and accept the developer terms.
3. **My Apps → Create app**.
   - Use case: the one about **Instagram** ("Manage messaging & content on
     Instagram").
   - App name: `7rage poster`. Finish creating it.
4. In the app's dashboard, open **Instagram → API setup with Instagram login**.
5. Under **Generate access tokens**, click **Add account** and log in as
   **@sevenrage7**. Approve the permissions (it needs
   `instagram_business_basic` and `instagram_business_content_publish`).
   - If it says the account must be a **tester** first: go to **App roles →
     Roles → Add people → Instagram Tester**, enter `sevenrage7`, then in the
     Instagram app accept the invite (Settings → Website permissions / Apps
     and websites → Tester invites). Then retry step 5.
6. Click **Generate token** next to @sevenrage7 and **copy the token**. This is
   your `IG_TOKEN`. It lasts 60 days, and the automation renews it every week.

You don't need Meta's app review; it's only needed when an app posts for
*other* people's accounts.

### 3b. If you only get a Facebook-login token (starts with `EA`)

This is the route that's used now. The automation turns it into a Page token
that never expires.

1. **Link @sevenrage7 to a Facebook Page.** It has to be a *Page*: linking
   Instagram to your Facebook *profile* in Accounts Center is not enough.
   - Create one at **facebook.com/pages/create** (name `7rage`, category
     "Digital creator"), using the same Facebook account you use on
     developers.facebook.com.
   - Switch into the Page → **Settings → Linked accounts → Instagram →
     Connect** → log in as @sevenrage7. (Or Meta Business Suite → Settings →
     Instagram accounts.)
2. **Get a token with the right permissions.** The easiest place is
   **developers.facebook.com/tools/explorer** (Graph API Explorer):
   - top right: pick your app (`7rage poster`)
   - "User or Page": **User Token**
   - Permissions: add `instagram_basic`, `instagram_content_publish`,
     `pages_show_list`, `pages_read_engagement` (and `business_management` if
     your Page is in a Business portfolio)
   - **Generate Access Token**. When Facebook asks, select the 7rage Page
     **and** the @sevenrage7 account. Copy the `EAA…` token.
3. **Get the app ID and secret:** your app → **App settings → Basic** → copy
   **App ID**, then click **Show** next to **App secret** and copy it.
4. Add/update these repo secrets (Settings → Secrets and variables → Actions):

   | Name | Value |
   |---|---|
   | `IG_TOKEN` | the `EAA…` token |
   | `META_APP_ID` | the App ID |
   | `META_APP_SECRET` | the App secret |

5. **Within the hour** (tokens from the Explorer expire in 1–2 hours), go to
   **Actions → Connect Instagram (one-time) → Run workflow**. It replaces
   `IG_TOKEN` with a never-expiring Page token and saves `IG_USER_ID`. The log
   should end with `Done. Posts will go to @sevenrage7.` If it says a
   permission or the Page link is missing, fix that and repeat steps 2, 4 and 5.

Needs `SECRETS_PAT` from step 5 below, so create that first.

## 4. Get the Claude key, for writing new lines (5 min)

1. Go to **console.anthropic.com**, sign up, and add a small amount of credit
   ($5 lasts years at this usage: one batch of 50 lines costs a few cents).
2. **API keys → Create key** → copy it. This is your `ANTHROPIC_API_KEY`.

## 5. Make a key that lets the automation renew the Instagram token (5 min)

1. On github.com: your profile picture → **Settings → Developer settings →
   Personal access tokens → Fine-grained tokens → Generate new token**.
2. Name: `7rage token renewer`. Expiration: **No expiration** if offered,
   otherwise the longest option (set a calendar reminder to renew it).
3. Repository access: **Only select repositories → 7rage**.
4. Permissions → Repository permissions → **Secrets: Read and write**.
5. Generate and **copy it**. This is your `SECRETS_PAT`.

## 6. Paste the 3 keys into the repo (2 min)

In your repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add each one (name exactly as shown):

| Name | Value |
|---|---|
| `IG_TOKEN` | the Instagram token from step 3 |
| `ANTHROPIC_API_KEY` | the Claude key from step 4 |
| `SECRETS_PAT` | the GitHub token from step 5 |

## 7. Test it (5 min)

1. **Actions** tab → if asked, click **I understand my workflows, enable them**.
2. **Refresh Instagram token → Run workflow**. It should go green. That proves
   the Instagram key and the renewer key both work.
3. **Post to Instagram → Run workflow**. In the *now* box, type the current
   New York date with `T05:10`, for example `2026-11-12T05:10`. Click **Run**.
   ⚠️ **This posts for real.** Use it for your first post.
   - Both jobs should go green, and the post appears on @sevenrage7 within a
     minute or two.
   - A commit "posted 2026-…" appears in the repo. That's the bot recording
     what it posted.

Done. From now on it posts at about **12 AM, 5 AM, 10 AM, 12 PM, 4 PM and
7 PM New York time** every day (usually within 20 minutes of the slot).

---

## What it costs

| Thing | Cost |
|---|---|
| GitHub Actions + Pages (public repo) | free |
| Meta / Instagram API | free |
| Claude (about 1 batch of lines a month) | a few cents a month |
