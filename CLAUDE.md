# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Slack Trophy Leaderboard — aggregates top-reacted photos and messages from Slack channels and displays them as a ranked leaderboard with trophy/podium visuals.

## Running the Project

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Swagger UI: `http://localhost:8000/docs`

### Frontend (static, no build step)
```bash
cd frontend
python -m http.server 3000
```

### Environment Setup
Copy and populate `backend/.env`:
```
SLACK_USER_TOKEN=xoxp-...   # Required: user token (not bot token xoxb-)
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
CACHE_TTL=600               # seconds
SECRET_KEY=                 # optional: enables simple login page auth
```

## Architecture

**Backend** (`backend/app/`):
- `main.py` — FastAPI app, all route handlers, CORS middleware
- `slack_client.py` — `SlackClient` singleton; wraps slack-sdk, handles channel listing, history pagination, photo/video/message extraction, reaction counting
- `cache.py` — Thread-safe in-memory TTL cache (not Redis); global `cache` singleton used directly from routes
- `config.py` — Settings loaded from env vars via `dotenv`; `settings` singleton
- `models.py` — Pydantic models for all API I/O (`Channel`, `Photo`, `Message`, response wrappers)
- `utils.py` — Input validation (`validate_channel_id`, `parse_date_range`), file type helpers (`is_image_file`, `is_video_file`, `get_media_type`)

**Frontend** (`frontend/`):
- `js/api.js` — All `fetch()` calls to the backend; `API_BASE_URL` constant here; includes `getPermalink`, `getProxyImageUrl`, `getEmojiInfo` helpers
- `js/ui.js` — DOM rendering (cards, podium, modals, toasts)
- `js/app.js` — App state (`currentChannels`, `currentItems`), event wiring, orchestration; currently fetches photos only (not messages) on filter apply
- `js/auth.js` — Handles `SECRET_KEY` login flow (only active when backend has `SECRET_KEY` set)
- No bundler; files are loaded directly via `<script>` tags in `index.html`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/verify` | Verify `SECRET_KEY` for auth |
| GET | `/channels` | List filtered Slack channels |
| GET | `/photos` | Top-reacted photos/videos for a channel+date range; supports `unique_reactions` and `debug` query params |
| GET | `/messages` | Top-reacted text messages for a channel+date range; supports `unique_reactions` |
| GET | `/proxy-image` | Proxy any Slack media URL (images and videos) with auth headers |
| GET | `/permalink` | Get Slack permalink for a message by `channel_id` + `message_ts` |
| GET | `/emoji-info` | Look up custom emoji URL by name via `emoji.list` API |
| GET | `/debug/messages` | Raw Slack message structure for a channel+date range — useful when investigating missing photos |

## Key Behaviors to Know

**Channel filtering**: `SlackClient.get_channels()` only returns channels whose names contain keywords defined in the `allowed_keywords` list (`backend/app/slack_client.py:38`). Current keywords: `general`, `privatekotha`, `internal-development`, `life-at-strativ`. Add keywords there to expose additional channels.

**Photo/video extraction**: `extract_photos` handles both images and videos. Thread messages are NOT skipped (that logic is commented out). Photos with 0 reactions are dropped. For videos, a Slack-generated thumbnail (`thumb_video`, `thumb_480`, etc.) is used as `thumbnail_url`.

**User info enrichment**: Both `Photo` and `Message` objects include full name fields (`uploader_full_name`, `author_full_name`). `Photo` also includes `uploader_email` and `uploader_profile_photo` (fetched via `users_info` per message — no batching).

**Proxy URLs pre-populated on backend**: The `/photos` route sets `proxy_url` and `proxy_thumbnail_url` on each `Photo` before returning, so external consumers (e.g. n8n) can access media without Slack auth. The frontend can also construct proxy URLs via `getProxyImageUrl()` in `api.js`.

**Reaction counting modes**:
- Default: sum all reaction counts per message (a user reacting 3 times = 3)
- Unique: count distinct users who reacted per message; uses a sentinel key `__total_unique_people__` internally that is stripped before returning

**Caching strategy**: Channel list is hard-cached for 1 hour. For photos/messages, metadata is cached but reactions are always re-fetched from Slack on every request and merged via `update_photo_reactions` / `update_message_reactions`.
