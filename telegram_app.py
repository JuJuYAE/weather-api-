from dotenv import load_dotenv
import os, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

token = os.getenv("TELEGRAM_TOKEN")

async def start(update, context):
    user = update.effective_user
    chat_id = update.effective_chat.id
     
    await update.message.reply_text("Welcome to OpenCourt's TeleBot. Right now we only send weekly weather notifications but expect more updates from us soon.")

def main():
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()