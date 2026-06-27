import os
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from praisonaiagents import Agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FREELLM_API_KEY = os.environ.get("FREELLM_API_KEY")
FREELLM_BASE_URL = os.environ.get("FREELLM_BASE_URL")
ALLOWED_USER_ID = os.environ.get("ALLOWED_USER_ID", "")

os.environ["OPENAI_API_KEY"] = FREELLM_API_KEY or ""
os.environ["OPENAI_API_BASE"] = FREELLM_BASE_URL or ""
os.environ["OPENAI_MODEL_NAME"] = "auto"

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

def is_allowed(update: Update) -> bool:
    if not ALLOWED_USER_ID:
        return True
    return str(update.effective_user.id) == ALLOWED_USER_ID

def run_agent(user_message):
    agent = Agent(
        instructions="""You are G.one — a powerful AI assistant. 
        You can help with research, analysis, writing, coding, and complex tasks.
        Always respond in the same language the user writes in.""",
        llm="auto",
    )
    response = agent.start(user_message)
    return response

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Access denied.")
        return
    await update.message.reply_text(
        "Namaste! Main G.one hoon — tumhara powerful AI agent! 🤖\n\nKuch bhi pucho — research, analysis, coding, writing — sab kar sakta hoon!"
    )

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("G.one alive hai! ✅")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("Access denied.")
        return

    user_message = update.message.text
    logger.info(f"Message: {user_message}")
    await update.message.reply_text("Soch raha hoon... ⏳")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: run_agent(user_message))
        if response:
            await update.message.reply_text(str(response))
        else:
            await update.message.reply_text("Kuch issue hua, dobara try karo.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN nahi mili!")

    threading.Thread(target=run_health_server, daemon=True).start()
    logger.info("Health server started")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("G.one bot chal raha hai...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
