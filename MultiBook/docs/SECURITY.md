# Security

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly.

## Environment Variables & Secrets

Never commit real credentials to the repository. Use:

- `backend/.env` (gitignored) for Django backend
- `frontend/.env.local` (gitignored) for Next.js frontend
- Copy from `backend/.env.example` and `frontend/.env.example` — replace placeholders only

## If Credentials Were Exposed

If you suspect credentials were committed to git history:

1. **Rotate immediately** — revoke and regenerate all exposed keys:
   - Google OAuth client secrets (Google Cloud Console)
   - Gmail/SMTP app passwords (Google Account → Security)
   - Supabase keys (Supabase Dashboard → Settings → API)
   - Database passwords (Supabase → Settings → Database)
   - Any other API keys

2. **Update `.env`** on all servers with new values

3. **Consider history rewrite** — use `git filter-repo` or BFG Repo Cleaner to remove secrets from history (requires force push; coordinate with team)

## Best Practices

- Use environment variables for all secrets
- Never log credentials
- Use `.env.example` with placeholders only (e.g. `YOUR_EMAIL`, `YOUR_GMAIL_APP_PASSWORD`)
- Rotate keys periodically
