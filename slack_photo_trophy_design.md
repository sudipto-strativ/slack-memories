# Slack Photo Trophy System
## System Design & Requirements Document

---

## 1. Executive Summary

**Project Name:** Slack Photo Trophy - Emoji Champion Leaderboard

**Purpose:** A celebratory system that aggregates and showcases the highest-rated photos from Slack channels within a specified date range, displaying them as "digital trophies" with reaction counts. The system promotes team engagement and celebrates memorable moments with an engaging, celebratory UI.

**Key Features:**
- Slack channel selection and date range filtering
- Photo extraction from Slack messages
- Emoji reaction counting (with duplicate vs. unique reaction toggle)
- Trophy-style display with visual hierarchy
- Responsive, modern UI built with Bootstrap 5

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
Frontend (Bootstrap 5)
    ↓
FastAPI Backend
    ↓
Slack API Client
    ↓
Slack Workspace
```

### 2.2 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | HTML5, CSS3, JavaScript (ES6+) | - |
| Frontend Framework | Bootstrap | 5.x |
| Backend | FastAPI | Latest |
| Async Support | Uvicorn | Latest |
| Slack Integration | slack-sdk | Latest |
| Python | Python | 3.9+ |

---

## 3. Functional Requirements

### 3.1 Frontend Requirements

#### 3.1.1 UI Components

**Header Section:**
- Application title with trophy icon/emoji (🏆)
- Tagline: "Celebrate Your Most Loved Moments"
- Visual theme: Gold/bronze/silver gradient or celebratory colors

**Filter Panel:**
- Slack channel selector (dropdown, populated from available channels)
- Date range picker (from date, to date with calendar UI)
- Leaderboard type selector (radio buttons or toggle):
  - Option 1: "Top Photos" - ranked by emoji reactions on photos only
  - Option 2: "Top Messages" - ranked by emoji reactions on text messages only
- "Unique Reactions Only" toggle checkbox (applies to both leaderboard types)
- "Apply Filters" button with loading state

**Results Section:**
- Photo/Message gallery displaying items sorted by emoji count (highest to lowest)
- Each card displays (for Top Photos mode):
  - Photo image
  - Emoji breakdown (count per emoji type, e.g., 👍: 15, ❤️: 12, etc.)
  - Total reaction count badge (prominent positioning)
  - Medal indicator (🥇 🥈 🥉 for top 3)
  - Optional: Photo context (timestamp, uploader username if available)
- Each card displays (for Top Messages mode):
  - Message text (truncated if necessary, expandable)
  - Emoji breakdown
  - Total reaction count badge
  - Medal indicator
  - Message metadata (author, timestamp)
- Empty state message with illustration if no photos found

**Visual Polish:**
- Confetti animation on page load (optional, libraries like canvas-confetti)
- Smooth card animations (hover effects, fade-in on load)
- Color-coded medals for ranking
- Emoji reaction pills/badges with color coding

#### 3.1.2 User Interactions

- Select channel → system auto-populates available photos
- Select date range → filters results in real-time or on button click
- Toggle "Unique Reactions" checkbox → re-fetches data with unique user constraint
- Click on photo card → modal showing full photo, detailed emoji breakdown, timestamp
- Responsive design: works seamlessly on desktop, tablet, mobile

#### 3.1.3 Error Handling & States

- Loading state: skeleton cards or spinner
- No results state: friendly message with suggestions
- Error state: display error message with retry button
- Network error: graceful fallback with offline message

### 3.2 Backend Requirements

#### 3.2.1 API Endpoints

**GET `/channels`**
- Returns list of available Slack channels user has access to
- Response: `{ channels: [{ id, name }, ...] }`

**GET `/photos`**
- Query Parameters:
  - `channel_id`: Required, Slack channel ID
  - `start_date`: Required, ISO 8601 format (YYYY-MM-DD)
  - `end_date`: Required, ISO 8601 format (YYYY-MM-DD)
  - `unique_reactions`: Boolean (default: false)
    - `true`: Count only one reaction per user per item
    - `false`: Count all reactions (user can react multiple times)
- Response: `{ items: [{ url, emoji_counts: { emoji: count, ... }, total_reactions, timestamp }, ...] }`
- Returns photos sorted by total_reactions descending
- Note: Excludes thread messages (only processes main channel messages)

**GET `/messages`**
- Query Parameters:
  - `channel_id`: Required, Slack channel ID
  - `start_date`: Required, ISO 8601 format (YYYY-MM-DD)
  - `end_date`: Required, ISO 8601 format (YYYY-MM-DD)
  - `unique_reactions`: Boolean (default: false)
    - `true`: Count only one reaction per user per message
    - `false`: Count all reactions
- Response: `{ items: [{ text, author, emoji_counts: { emoji: count, ... }, total_reactions, timestamp }, ...] }`
- Returns messages sorted by total_reactions descending
- Note: Excludes thread messages (only processes main channel messages)

**GET `/health`**
- Simple health check endpoint
- Response: `{ status: "ok" }`

#### 3.2.2 Slack Integration

- Use `slack_sdk` library for Slack API communication
- Fetch channel list via `conversations.list()` (public channels) or `groups.list()` (private channels)
- Iterate through messages in date range using `conversations.history()`
- **Important:** Use `include_all_metadata: false` and filter out messages with `thread_ts` (thread messages) - only process root/main channel messages
- Extract messages with file/image attachments or embedded images (for photos)
- Extract text messages without attachments (for messages)
- Parse reactions via message metadata
- Filter photos to include only image files (mime type checking)

#### 3.2.3 Data Processing

**Photo Extraction Logic:**
```
For each message in channel within date range:
  If message.thread_ts exists:
    SKIP (ignore thread messages)
  If message has files or attachments:
    If file is image/photo (jpg, png, gif, webp):
      Store: {
        url: file_permalink,
        timestamp: message_timestamp,
        channel_id: channel_id,
        uploader: message_user
      }
```

**Message Extraction Logic:**
```
For each message in channel within date range:
  If message.thread_ts exists:
    SKIP (ignore thread messages)
  If message has text AND no files/attachments:
    Store: {
      text: message_text,
      author: message_user,
      timestamp: message_timestamp,
      channel_id: channel_id
    }
```

**Reaction Counting Logic:**
```
If unique_reactions = false:
  Count all reactions from all users
  Sum emoji counts across all users for each emoji type
  
If unique_reactions = true:
  For each emoji type:
    Count unique users who reacted with that emoji
    Only count 1 per user per emoji per photo
```

#### 3.2.4 Caching Strategy

- Cache channel list (refresh every 1 hour)
- Cache photo results (with cache key = channel_id + start_date + end_date + unique_flag + "photos")
- Cache message results (with cache key = channel_id + start_date + end_date + unique_flag + "messages")
- Cache duration: 10 minutes for fresh data
- Implement cache invalidation on manual refresh

---

## 4. Non-Functional Requirements

### 4.1 Performance

- Page load time: < 2 seconds for typical queries
- API response time: < 3 seconds for photos endpoint
- Support up to 500 photos per query without degradation
- Image lazy loading for gallery (progressive display)

### 4.2 Scalability

- Backend should handle concurrent requests
- Rate limiting: implement to respect Slack API limits (60 requests/minute typically)
- Database consideration: Optional Redis for caching

### 4.3 Security

- Slack token stored securely (environment variables, not in code)
- Validate channel_id input to prevent injection attacks
- Validate date ranges (prevent DoS from requesting 10-year ranges)
- CORS configuration: allow frontend domain only
- Input sanitization for all query parameters

### 4.4 Availability

- Graceful degradation if Slack API is unavailable
- Friendly error messages to users
- Health check endpoint for monitoring

### 4.5 User Experience

- Responsive design: Desktop, tablet, mobile
- Accessibility: WCAG 2.1 AA standard (alt text for images, proper color contrast)
- Dark mode support (optional but recommended)

---

## 5. Data Model

### 5.1 Photo Object

```json
{
  "id": "unique_photo_id",
  "url": "https://slack_cdn.com/file.jpg",
  "channel_id": "C1234567890",
  "timestamp": "1234567890.000100",
  "uploader_name": "john_doe",
  "emoji_reactions": {
    "👍": 25,
    "❤️": 18,
    "🎉": 12,
    "😂": 8,
    "🔥": 5
  },
  "total_reactions": 68,
  "rank": 1
}
```

### 5.2 Message Object

```json
{
  "id": "unique_message_id",
  "text": "Just shipped the new feature!",
  "author_name": "jane_smith",
  "channel_id": "C1234567890",
  "timestamp": "1234567890.000100",
  "emoji_reactions": {
    "👍": 32,
    "🎉": 28,
    "🚀": 15,
    "❤️": 12
  },
  "total_reactions": 87,
  "rank": 1
}
```

### 5.3 Channel Object

```json
{
  "id": "C1234567890",
  "name": "announcements",
  "is_private": false
}
```

---

## 6. UI/UX Design Specifications

### 6.1 Design Philosophy

**Theme:** Celebratory, trophy-like, energetic

**Color Palette:**
- Primary: Gold (#FFD700)
- Secondary: Silver (#C0C0C0)
- Accent: Bronze (#CD7F32)
- Background: Dark slate or light neutral
- Text: High contrast for accessibility

**Typography:**
- Headers: Bold, large, celebratory (font-family: montserrat, sans-serif)
- Body: Clean, readable (font-family: inter, sans-serif)

### 6.2 Layout Wireframe

```
┌─────────────────────────────────────────┐
│  🏆 SLACK TROPHY LEADERBOARD            │
│     Celebrate Your Most Loved Moments   │
├─────────────────────────────────────────┤
│ [Channel ▼] [Date Range ▼]              │
│ ◉ Top Photos  ○ Top Messages            │
│ [☐ Unique] [Apply Filters ▶]            │
├─────────────────────────────────────────┤
│  🥇 Item 1         🥈 Item 2  🥉 Pg 3  │
│  👍 25  ❤️ 18       👍 15  ❤️ 20 ...    │
│  68 reactions       52 reactions        │
├─────────────────────────────────────────┤
│  #4 Item 4         #5 Item 5  ...       │
│  40 reactions       35 reactions        │
└─────────────────────────────────────────┘
```

### 6.3 Interactive Elements

- **Hover Effects:** Card elevation, shadow expansion, slight scale increase
- **Animations:** Fade-in on load, slide transitions between filters
- **Loading:** Pulsing skeleton cards or animated spinner
- **Feedback:** Toast notifications for errors/success

### 6.4 Engagement Features

**Medal Rankings:**
- Top 3 photos receive visual medals (🥇 🥈 🥉)
- Gold background for #1, silver for #2, bronze for #3
- Animated badge with shine effect

**Emoji Breakdown:**
- Display top 5 emojis used for each photo
- Show count next to each emoji
- Visual bar chart or pill-style indicators

**"Podium" View** (Optional Enhancement):
- Show top 3 photos in a podium arrangement with staggered heights
- Position #2 on left, #1 center (elevated), #3 on right
- Celebrate visually below top 3 are smaller cards

**Share Button** (Optional):
- Generate shareable trophy image/link
- "Share Your Trophy" button for social engagement

---

## 7. Implementation Phases

### Phase 1: MVP (Week 1-2)
- Basic FastAPI backend with Slack integration
- Channel listing endpoint
- Photo and message fetching with basic emoji counting
- Thread message filtering (exclude thread_ts messages)
- Simple Bootstrap UI with filters
- Radio button selector for Top Photos vs Top Messages
- Date range and unique reactions toggle
- Display appropriate data based on selected leaderboard type

### Phase 2: Polish (Week 3)
- Improved UI with medal rankings
- Emoji breakdown display
- Loading states and error handling
- Responsive design refinement
- Caching implementation

### Phase 3: Enhancements (Week 4+)
- Podium view for top 3
- Share functionality
- Advanced filtering (emoji type filters)
- Analytics dashboard (trending photos over time)
- Dark mode
- Photo modal with detailed breakdown

---

## 8. Deployment & Setup

### 8.1 Prerequisites

- Slack App with appropriate permissions
- Python 3.9+
- Node.js (optional, for frontend build tools)

### 8.2 Required Slack Permissions

```
- channels:read
- channels:history
- reactions:read
- files:read
- users:read
```

### 8.3 Environment Variables

```
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
CACHE_TTL=600
```

### 8.4 Running Locally

```bash
# Backend
pip install fastapi uvicorn slack-sdk
uvicorn main:app --reload

# Frontend
# Serve static files from /static directory
# Use live-server or Python's http.server
```

---

## 9. Future Enhancements

- **AI Integration:** Auto-generate captions for top photos
- **Recurring Reports:** Email weekly trophy summaries
- **Custom Reactions:** Allow teams to define custom trophy criteria
- **Multi-workspace Support:** Aggregate across multiple Slack workspaces
- **Export:** Download trophy leaderboard as PDF/image
- **Timeline View:** See photo trophy evolution over months
- **Gamification:** User profiles, achievement badges, points system

---

## 10. Acceptance Criteria

- ✅ Users can select a Slack channel
- ✅ Users can select a date range
- ✅ Users can choose between "Top Photos" or "Top Messages" leaderboard
- ✅ System displays photos/messages sorted by emoji count (highest first)
- ✅ Thread messages are excluded from results
- ✅ "Unique Reactions" toggle works correctly for both leaderboard types
- ✅ Top 3 items are visually distinguished with medals
- ✅ UI is responsive and works on mobile/tablet/desktop
- ✅ Loading states are visible
- ✅ Error messages are user-friendly
- ✅ API response time < 3 seconds
- ✅ All images lazy load for performance

---

## 11. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Slack API rate limits | High | Implement caching, batching requests |
| Large photo volume | Medium | Pagination, lazy loading, indexing |
| Slow image delivery | Medium | Use Slack CDN directly, image optimization |
| Slack token exposure | Critical | Use environment variables, secrets manager |
| Missing Slack permissions | Medium | Clear setup guide, permission check endpoint |

---

## 12. Success Metrics

- System loads photos in < 2 seconds
- 95% uptime
- Zero security vulnerabilities
- User satisfaction > 4.5/5 (if surveyed)
- Engagement: 80%+ teams use monthly

