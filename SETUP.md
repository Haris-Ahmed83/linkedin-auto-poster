# LinkedIn Auto-Poster — Setup Guide

## Step 1: Push This Repo to GitHub

```bash
git init
git add .
git commit -m "Initial commit: LinkedIn auto-poster"
git remote add origin https://github.com/Haris-Ahmed83/linkedin-auto-poster.git
git push -u origin main
```

## Step 2: Generate LinkedIn OAuth Token

1. Go to https://www.linkedin.com/developers/apps/YOUR_APP_ID/auth
2. Under "OAuth 2.0 settings", add redirect URL:
   `https://haris.primevoai.com/callback`
3. Open this URL in your browser (replace CLIENT_ID):

```
https://www.linkedin.com/oauth/v2/authorization?
response_type=code&
client_id=779zgdewb7kogo&
redirect_uri=https://haris.primevoai.com/callback&
scope=w_member_social%20openid%20profile%20email&
state=123456
```

4. After authorizing, you'll be redirected to a URL like:
   `https://haris.primevoai.com/callback?code=AUTHORIZATION_CODE`

5. Copy the `code` parameter value. Then run:

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "client_id=779zgdewb7kogo" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://haris.primevoai.com/callback"
```

6. You'll get JSON back with `access_token` and `refresh_token`.

## Step 3: Get Your LinkedIn User URN

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.linkedin.com/v2/userinfo
```

You'll get back something like:
```json
{"sub": "12345abc"}
```

Your URN is: `urn:li:person:12345abc`

## Step 4: Set GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value |
|---|---|
| `GH_TOKEN` | Your GitHub token (already you have) |
| `LINKEDIN_CLIENT_ID` | `779zgdewb7kogo` |
| `LINKEDIN_CLIENT_SECRET` | Your client secret (from LinkedIn dev app) |
| `LINKEDIN_ACCESS_TOKEN` | From Step 2 |
| `LINKEDIN_REFRESH_TOKEN` | From Step 2 |
| `LINKEDIN_USER_URN` | From Step 3 |

## Step 5: Configure Posting

In `scripts/config.py`, change:
- `DRY_RUN = True` → `DRY_RUN = False` (after you approve the first drafts)
- Adjust `POSTING_DAYS` and `POSTING_TIMES_PKT` if needed

## Step 6: Verify

Go to GitHub repo → Actions tab → "LinkedIn Auto Poster" → Run workflow (manual trigger first)

## Schedule (After Verification)

The workflow runs automatically:
- **Tuesday** 8:30 AM PKT → Local audience
- **Wednesday** 3:00 PM PKT → UK morning + US audience
- **Thursday** 8:30 AM PKT → Local audience
