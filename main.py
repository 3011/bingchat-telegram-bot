import re
import time
import asyncio
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
import bing


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

conversation_style = "balanced"  # 默认对话风格
bot_token = ""  # 机器人的token
allowed_users = []  # 允许使用机器人的用户的id，建议个人使用
message_update_time = 1.5  # 回复的更新间隔时间

lock = asyncio.Lock()


async def reset_reply(reply_message, more=""):
    await bing.reset_chat()
    await reply_message(
        text="Conversation has been reset.\nConversation style is %s.%s"
        % (
            conversation_style,
            more,
        )
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in allowed_users:
        await update.message.reply_text(text="You are not allowed to use this bot.")
        return

    await reset_reply(update.message.reply_text)


async def handle_bing_reply(res):
    source_button_keyboard = []
    if "sourceAttributions" in res["item"]["messages"][1]:
        for source in res["item"]["messages"][1]["sourceAttributions"]:
            source_button_keyboard.append(
                [source["providerDisplayName"], source["seeMoreUrl"]]
            )
    inline_keyboard = []
    for source_button in source_button_keyboard:
        inline_keyboard.append(
            [InlineKeyboardButton(text=source_button[0], url=source_button[1])]
        )
    return (
        re.sub(r"\[\^(\d+)\^\]", r"", res["item"]["messages"][1]["text"]),
        inline_keyboard,
    )


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in allowed_users:
        await update.message.reply_text(text="You are not allowed to use this bot.")
        return

    message = update.message.text
    reply_message = await update.message.reply_text(text="Bing is typing...")

    try:
        prev_time = time.time()
        prev_reply_text = ""
        async for is_done, res in bing.get_reply_stream(message):
            if is_done:
                try:
                    reply_text, inline_keyboard = await handle_bing_reply(res)
                    if reply_text.strip() != prev_reply_text.strip() or inline_keyboard:
                        await reply_message.edit_text(
                            text=reply_text,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard),
                        )
                except Exception as err:
                    print(err)
                    try:
                        await reply_message.edit_text(
                            text="[Default ParseMode]\n" + reply_text
                        )
                    except:
                        await reset_reply(
                            reply_message.edit_text, more="\n\nError in done."
                        )
            else:
                if time.time() - prev_time > message_update_time and res:
                    prev_time = time.time()
                    try:
                        prev_reply_text = res
                        await reply_message.edit_text(
                            text=res,
                        )
                    except:
                        await reset_reply(
                            reply_message.edit_text, more="\n\nError in not done."
                        )
    except:
        await reset_reply(reply_message.edit_text)


async def creative(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in allowed_users:
        await update.message.reply_text(text="You are not allowed to use this bot.")
        return

    global conversation_style
    conversation_style = "creative"
    await update.message.reply_text(
        text="Conversation style is %s." % conversation_style
    )


async def balanced(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in allowed_users:
        await update.message.reply_text(text="You are not allowed to use this bot.")
        return

    global conversation_style
    conversation_style = "balanced"
    await update.message.reply_text(
        text="Conversation style is %s." % conversation_style
    )


async def precise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in allowed_users:
        await update.message.reply_text(text="You are not allowed to use this bot.")
        return

    global conversation_style
    conversation_style = "precise"
    await update.message.reply_text(
        text="Conversation style is %s." % conversation_style
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("creative", creative))
    application.add_handler(CommandHandler("balanced", balanced))
    application.add_handler(CommandHandler("precise", precise))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    application.run_polling()
