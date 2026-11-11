"""One-time: turn a Facebook-login token (EAA...) into a never-expiring Page token for @sevenrage7.

Steps:
  1. swap the (possibly short-lived) token for a 60-day one, using the app ID and secret
  2. list the Facebook Pages it can manage and find the one linked to the Instagram account
  3. take that Page's token: one made from a 60-day user token doesn't expire
  4. check it has publishing permission, then save IG_TOKEN and IG_USER_ID as repo secrets

Env: IG_TOKEN, META_APP_ID, META_APP_SECRET, GH_TOKEN (a token allowed to write secrets),
     IG_USERNAME (default sevenrage7). --dry prints instead of saving secrets.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

FB = os.environ.get("FB_API_BASE", "https://graph.facebook.com") + "/" + os.environ.get("IG_API_VERSION", "v24.0")
NEEDED = {"instagram_basic", "instagram_content_publish", "pages_show_list"}


def get(path, **params):
    url = f"{FB}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:400]
        sys.exit(f"Facebook API error on {path}: {e.code} {msg}")


def mask(value):
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::add-mask::{value}")


def save_secret(name, value):
    if "--dry" in sys.argv:
        print(f"[dry] would set secret {name} ({len(value)} chars)")
        return
    subprocess.run(["gh", "secret", "set", name, "--body", value,
                    "--repo", os.environ["GITHUB_REPOSITORY"]], check=True)
    print(f"saved secret {name}")


def main():
    tok = os.environ.get("IG_TOKEN", "").strip()
    app_id = os.environ.get("META_APP_ID", "").strip()
    secret = os.environ.get("META_APP_SECRET", "").strip()
    want = os.environ.get("IG_USERNAME", "sevenrage7").strip().lstrip("@").lower()
    if not tok:
        sys.exit("IG_TOKEN secret is empty. Paste your EAA... token into it first.")
    if tok.startswith("IG"):
        print("IG_TOKEN is an Instagram-login token (IGAA...). Nothing to connect; posting works as is.")
        return
    if not (app_id and secret):
        sys.exit("META_APP_ID and META_APP_SECRET secrets are needed (Meta app → App settings → Basic).")

    print("1/4 exchanging for a long-lived token...")
    long_user = get("oauth/access_token", grant_type="fb_exchange_token", client_id=app_id,
                    client_secret=secret, fb_exchange_token=tok)["access_token"]
    mask(long_user)

    print("2/4 looking for the Facebook Page linked to Instagram...")
    fields = "name,access_token,instagram_business_account{id,username}"
    pages = get("me/accounts", fields=fields, limit=100, access_token=long_user).get("data", [])

    # Pages inside a Business portfolio often don't show up in me/accounts. The token's
    # granular scopes still list the Page IDs it was granted, so ask for those directly.
    info = get("debug_token", input_token=long_user, access_token=f"{app_id}|{secret}").get("data", {})
    granted = sorted(info.get("scopes", []))
    page_ids = {t for g in info.get("granular_scopes", []) if g.get("scope", "").startswith("pages_")
                for t in g.get("target_ids", [])}
    known = {p.get("id") for p in pages}
    for pid in sorted(page_ids - known):
        p = get(pid, fields=fields, access_token=long_user)
        if p.get("access_token"):
            pages.append(p)

    linked = [p for p in pages if p.get("instagram_business_account")]
    if not linked:
        names = ", ".join(p.get("name", "?") for p in pages) or "none"
        sys.exit("No Facebook Page with a linked Instagram account was found.\n"
                 f"  Pages this token can see: {names}\n"
                 f"  Permissions the token has: {', '.join(granted) or 'none'}\n"
                 f"  Page IDs it was granted: {', '.join(sorted(page_ids)) or 'none'}\n"
                 "Fix, depending on the above:\n"
                 "  - 'Pages ... none' and no Page IDs: when generating the token, tick the 7rage Page in "
                 "Facebook's popup (to redo the popup: Facebook → Settings → Business integrations → remove "
                 "the app, then generate again). Add business_management if the Page is in a Business portfolio.\n"
                 "  - Page listed but this still fails: link @sevenrage7 to that Page (Page settings → "
                 "Linked accounts → Instagram).\n"
                 "  - pages_show_list missing from permissions: add it in Graph API Explorer and regenerate.")
    page = next((p for p in linked if p["instagram_business_account"].get("username", "").lower() == want),
                linked[0])
    acct = page["instagram_business_account"]
    page_token = page["access_token"]
    mask(page_token)
    print(f"    found Page '{page['name']}' → @{acct.get('username')} (id {acct['id']})")

    print("3/4 checking the Page token...")
    info = get("debug_token", input_token=page_token, access_token=f"{app_id}|{secret}").get("data", {})
    scopes = set(info.get("scopes", []))
    expires = info.get("expires_at", 0)
    print(f"    expires: {'never' if not expires else expires}; permissions: {', '.join(sorted(scopes))}")
    missing = NEEDED - scopes
    if missing:
        sys.exit(f"The token is missing these permissions: {', '.join(sorted(missing))}.\n"
                 "Generate a new token with them ticked (see SETUP.md), paste it into IG_TOKEN, run again.")
    get(acct["id"], fields="username", access_token=page_token)  # proves it can reach the account

    print("4/4 saving secrets...")
    save_secret("IG_TOKEN", page_token)
    save_secret("IG_USER_ID", acct["id"])
    print(f"Done. Posts will go to @{acct.get('username')}.")


if __name__ == "__main__":
    main()
