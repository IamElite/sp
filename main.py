import asyncio
import threading

from datetime import date

from flask import Flask, jsonify, request

from config.settings import Config
from database.mongo import db
from services.telegram_service import TelegramService
from utils.logger import setup_logger
from worker import Worker

import bot.handlers.start
import bot.handlers.upload
import bot.commands.admin
import bot.commands.user
import bot.callbacks.manager

logger = setup_logger("main")

app = Flask(__name__)
tg = TelegramService()
worker = Worker()


@app.route("/")
def health():
    db_ok = db.is_connected
    status = "healthy" if db_ok else "degraded"
    return jsonify({
        "status": status,
        "database": "connected" if db_ok else "disconnected",
    }), 200 if db_ok else 503


@app.route("/releases")
def list_releases():
    limit = request.args.get("limit", 20, type=int)
    docs = list(
        db.releases.find({}, {"_id": 1, "title": 1, "episode": 1, "quality": 1, "release_date": 1, "processed": 1})
        .sort("release_date", -1)
        .limit(min(limit, 100))
    )
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify({"total": len(docs), "releases": docs})


@app.route("/releases/today")
def today_releases():
    today_str = date.today().strftime("%d %b %Y")
    docs = list(
        db.releases.find(
            {"release_date": {"$regex": today_str, "$options": "i"}},
            {"_id": 1, "title": 1, "episode": 1, "quality": 1, "release_date": 1, "processed": 1},
        ).sort("release_date", -1)
    )
    for d in docs:
        d["_id"] = str(d["_id"])
    return jsonify({"date": today_str, "total": len(docs), "releases": docs})


def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())


async def start_bot():
    try:
        db.connect()
        await tg.start()
        worker.tg = tg
        logger.info("Bot started — listening for updates")

        worker_task = asyncio.create_task(worker.worker_loop())
        await asyncio.gather(worker_task)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await tg.stop()
        db.close()


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    app.run(host="0.0.0.0", port=Config.PORT)
