<p align="center">
  <a href="https://heroku.com/deploy?template=https://github.com/YOUR_USERNAME/subsplease-filestore-bypass">
    <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy to Heroku">
  </a>
</p>

# SubsPlease FileStore Bypass

A Telegram bot that tracks [SubsPlease](https://subsplease.org) anime releases, downloads them via magnet links, enriches metadata from Jikan (MyAnimeList) / AniList, and serves files through Telegram's native file share links — bypassing traditional filestore hosting.

---

## Features

- **RSS Polling** — automatically detects new SubsPlease releases
- **Batch Skip** — batch releases are ignored
- **Magnet Download** — downloads via aria2c
- **Metadata Enrichment** — fetches English title, synopsis, genres from Jikan/AniList
- **Smart Filename** — renames to `[S{season}-E{ep}] Title [quality] [ESUB] @tag.mkv`
- **Telegram File Share** — generates share links via bot deep-linking
- **Optional Encoding** — ffmpeg re-encoding with 4 quality presets
- **Admin Upload** — manual file upload with auto-rename
- **Stats & Logging** — /stats, /retry, /log commands

---

## Deploy on Heroku

1. Click the **Deploy to Heroku** button above
2. Fill in the required config vars:
   - `BOT_TOKEN` — from [@BotFather](https://t.me/botfather)
   - `API_ID` & `API_HASH` — from [my.telegram.org/apps](https://my.telegram.org/apps)
   - `OWNER_ID` — get it from [@userinfobot](https://t.me/userinfobot)
   - `DB_CHANNEL_ID` — create a channel, add your bot as admin, forward a message to [@getidsbot](https://t.me/getidsbot)
   - `MONGODB_URI` — from [MongoDB Atlas](https://cloud.mongodb.com) (free tier works)
3. Deploy and scale the dyno:
   ```bash
   heroku ps:scale web=1
   ```
4. Your bot is live!

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram Bot Token |
| `API_ID` | ✅ | — | Telegram API ID |
| `API_HASH` | ✅ | — | Telegram API Hash |
| `OWNER_ID` | ✅ | — | Admin user ID |
| `DB_CHANNEL_ID` | ✅ | — | Storage channel ID |
| `MONGODB_URI` | ✅ | — | MongoDB connection string |
| `DATABASE_NAME` | | `subsplease_bot` | Database name |
| `TARGET_CHAT_ID` | | — | Auto-post target chat |
| `FILE_SUFFIX_TAG` | | `@SyntaxRealm` | Filename suffix tag |
| `ENCODING_ENABLED` | | `false` | Enable ffmpeg encoding |
| `AUTO_POST` | | `false` | Auto-post new releases |
| `RSS_FEED_URL` | | `https://subsplease.org/rss/` | RSS feed URL |
| `POLL_INTERVAL` | | `300` | Poll interval (seconds) |
| `LOG_LEVEL` | | `INFO` | Logging level |

---

## Manual Installation

```bash
git clone https://github.com/YOUR_USERNAME/subsplease-filestore-bypass.git
cd subsplease-filestore-bypass
pip install -r requirements.txt
cp config/sample.env .env
# edit .env with your values
python main.py
```

Requires **aria2c** for magnet downloads.

---

## License

MIT
