# 🏆 Slack Trophy Leaderboard

A celebratory system that aggregates and showcases the highest-rated photos and messages from Slack channels within a specified date range, displaying them as "digital trophies" with reaction counts.

## Features

- **Channel Selection**: Browse and select from available Slack channels
- **Date Range Filtering**: Filter results by custom date ranges
- **Dual Leaderboard Types**:
  - **Top Photos**: Ranked by emoji reactions on photos
  - **Top Messages**: Ranked by emoji reactions on text messages
- **Reaction Counting**: Toggle between all reactions and unique reactions per user
- **Trophy Display**: Visual medals (🥇 🥈 🥉) for top 3 items
- **Podium View**: Special display for top 3 items with staggered heights
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Modern UI**: Beautiful Bootstrap 5 interface with trophy-themed colors

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **slack-sdk**: Official Slack SDK for Python
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Frontend
- **Bootstrap 5**: CSS framework
- **Vanilla JavaScript (ES6+)**: No build step required
- **Canvas Confetti**: Celebratory animations

## Prerequisites

- Python 3.9 or higher
- Slack workspace with admin access
- Slack App with appropriate permissions

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd slack-trophy
```

### 2. Backend Setup

#### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Create Environment File

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your Slack credentials:

```env
SLACK_USER_TOKEN=xoxp-your-user-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
CACHE_TTL=600
```

**Note:** `SLACK_SIGNING_SECRET` is optional and only needed if you plan to use Slack webhooks.

#### Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI) will be available at `http://localhost:8000/docs`

### 3. Frontend Setup

The frontend is a static site that can be served in multiple ways:

#### Option A: Python HTTP Server

```bash
cd frontend
python -m http.server 3000
```

#### Option B: Node.js http-server

```bash
npm install -g http-server
cd frontend
http-server -p 3000
```

#### Option C: Any Static File Server

Serve the `frontend/` directory on port 3000 (or update `FRONTEND_URL` in backend `.env`)

### 4. Configure API URL (if needed)

If your backend is running on a different URL, update `API_BASE_URL` in `frontend/js/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## Slack App Configuration

### Step 1: Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name (e.g., "Trophy Leaderboard")
5. Select your workspace

### Step 2: Configure User Token Scopes

1. Go to **OAuth & Permissions** in the sidebar
2. Scroll to **Scopes** → **User Token Scopes**
3. Add the following scopes:
   - `channels:read` - View basic information about public channels
   - `channels:history` - View messages in public channels
   - `groups:read` - View basic information about private channels
   - `groups:history` - View messages in private channels
   - `reactions:read` - View emoji reactions
   - `files:read` - View files shared in channels
   - `users:read` - View people in the workspace

**Note:** User tokens use the permissions of the user who installs the app. The user must have access to the channels they want to analyze.

### Step 3: Install App to Workspace

1. Scroll to the top of **OAuth & Permissions**
2. Click **Install to Workspace**
3. Review permissions and click **Allow**
4. Copy the **User OAuth Token** (starts with `xoxp-`)
5. (Optional) Copy the **Signing Secret** from **Basic Information** → **App Credentials** if you plan to use webhooks

### Step 4: Update Environment Variables

Add the token to your `.env` file:

```env
SLACK_USER_TOKEN=xoxp-your-user-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

**Important Notes:**
- User tokens (`xoxp-`) represent the user who installed the app
- The app will have access to channels the installing user can access
- No need to add a bot to channels - user tokens use the user's own permissions
- User tokens may have different rate limits than bot tokens

## Usage

1. **Start the backend server** (see Backend Setup)
2. **Start the frontend server** (see Frontend Setup)
3. **Open your browser** to `http://localhost:3000`
4. **Select a channel** from the dropdown
5. **Choose a date range** using the date pickers
6. **Select leaderboard type**: Top Photos or Top Messages
7. **Toggle "Unique Reactions"** if you want to count only one reaction per user
8. **Click "Apply Filters"** to fetch and display results

### Features in Action

- **Medal Rankings**: Top 3 items display with 🥇 🥈 🥉 medals
- **Podium View**: Top 3 items are shown in a special podium layout
- **Emoji Breakdown**: See which emojis were used and their counts
- **Detail Modal**: Click any card to see full details
- **Share Functionality**: Share items using the share button in the modal

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

### `GET /channels`
Get list of available Slack channels.

**Response:**
```json
{
  "channels": [
    {
      "id": "C1234567890",
      "name": "general",
      "is_private": false
    }
  ]
}
```

### `GET /photos`
Get photos from a channel within a date range.

**Query Parameters:**
- `channel_id` (required): Slack channel ID
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format
- `unique_reactions` (optional): Boolean, default false

**Response:**
```json
{
  "items": [
    {
      "id": "1234567890.000100",
      "url": "https://...",
      "channel_id": "C1234567890",
      "timestamp": "1234567890.000100",
      "uploader_name": "john_doe",
      "emoji_reactions": {
        "👍": 25,
        "❤️": 18
      },
      "total_reactions": 43,
      "rank": 1
    }
  ]
}
```

### `GET /messages`
Get text messages from a channel within a date range.

**Query Parameters:**
- `channel_id` (required): Slack channel ID
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format
- `unique_reactions` (optional): Boolean, default false

**Response:**
```json
{
  "items": [
    {
      "id": "1234567890.000100",
      "text": "Message text here",
      "author_name": "jane_smith",
      "channel_id": "C1234567890",
      "timestamp": "1234567890.000100",
      "emoji_reactions": {
        "👍": 32,
        "🎉": 28
      },
      "total_reactions": 60,
      "rank": 1
    }
  ]
}
```

## Project Structure

```
slack-trophy/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration management
│   │   ├── models.py            # Pydantic models
│   │   ├── slack_client.py      # Slack API wrapper
│   │   ├── cache.py             # Caching implementation
│   │   └── utils.py             # Helper functions
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html               # Main HTML file
│   ├── css/
│   │   └── style.css            # Custom styles
│   ├── js/
│   │   ├── app.js              # Main application logic
│   │   ├── api.js              # API client
│   │   └── ui.js               # UI rendering functions
│   └── assets/                 # Images, icons
├── README.md
├── .gitignore
└── slack_photo_trophy_design.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SLACK_USER_TOKEN` | Slack user OAuth token (starts with `xoxp-`) | Required |
| `SLACK_SIGNING_SECRET` | Slack app signing secret (optional, for webhooks) | Optional |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `BACKEND_URL` | Backend URL | `http://localhost:8000` |
| `CACHE_TTL` | Cache time-to-live in seconds | `600` (10 minutes) |

### Cache Configuration

- Channel list: Cached for 1 hour
- Photo/message results: Cached for 10 minutes (configurable via `CACHE_TTL`)
- Cache keys include: channel_id, date range, unique_reactions flag, and item type

## Troubleshooting

### Backend Issues

**Error: "SLACK_USER_TOKEN environment variable is required"**
- Make sure your `.env` file exists in the `backend/` directory
- Verify the token starts with `xoxp-` (user token, not `xoxb-` bot token)

**Error: "Failed to fetch channels"**
- Check that your user token is valid
- Ensure the app is installed to your workspace
- Verify the user who installed the app has `channels:read` and `groups:read` scopes
- User tokens use the permissions of the installing user

**Error: "Failed to fetch channel history"**
- Make sure the user who installed the app has access to the channel
- Check that the user has `channels:history` or `groups:history` scope
- Verify the channel ID is correct
- User tokens can only access channels the installing user can access

### Frontend Issues

**Error: "Unable to connect to server"**
- Ensure the backend is running on port 8000
- Check that `API_BASE_URL` in `api.js` matches your backend URL
- Verify CORS is configured correctly in backend

**No channels in dropdown**
- Check browser console for errors
- Verify backend is running and accessible
- Check network tab for failed API requests

## Security Considerations

- **Never commit `.env` files** to version control
- **Keep Slack tokens secure** - rotate them if exposed
- **User tokens are tied to the installing user** - they have access to all channels the user can access
- **Use environment variables** for all sensitive data
- **Validate input** on both frontend and backend
- **Limit date ranges** to prevent DoS (max 1 year)
- **Configure CORS** to allow only your frontend domain
- **User tokens may have different rate limits** than bot tokens - be aware of API limits

## Performance

- **Caching**: Results are cached to reduce Slack API calls
- **Lazy Loading**: Images load only when visible
- **Pagination**: Consider implementing for large result sets
- **Rate Limiting**: Respect Slack API rate limits (60 requests/minute)

## Future Enhancements

- [ ] Multi-workspace support
- [ ] Export leaderboard as PDF/image
- [ ] Timeline view for photo evolution
- [ ] Advanced filtering (by emoji type)
- [ ] Analytics dashboard
- [ ] Recurring email reports
- [ ] Dark mode toggle
- [ ] User profiles and achievements

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the repository.

