import re
import time
import json
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

import bing as bot


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

conversation_style = "balanced"  # Default conversation style 默认对话风格
bot_token = ""  # Bot token 机器人token
allowed_users = []  # user_id(int) Allowed users, 允许使用机器人的用户的id，建议个人使用
message_update_time = 1.5  # (s) Message update time on reply 回复的更新间隔时间
retry_count = 3


async def reset_reply(reply_message, more=""):
    if more:
        more = "\n\n" + more
    await bot.reset_chat()
    await reply_message(
        text="%s - Conversation reset.%s"
        % (
            conversation_style.capitalize(),
            more,
        )
    )


async def handle_bing_reply(res):
    source_button_keyboard = []
    if "messages" not in res["item"]:
        raise Exception("The conversation may have been reset due to timeout.")

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
        re.sub(
            r"\[\^\d+\^\](\s(?=\[\^\d+\^\]))?", "", res["item"]["messages"][1]["text"]
        ),
        inline_keyboard,
    )


def check_user_id(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in allowed_users:
            await update.message.reply_text(text="You are not allowed to use this bot.")
            return
        return await func(update, context)

    return wrapper


@check_user_id
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reset_reply(update.message.reply_text)


@check_user_id
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for i in range(retry_count + 1):
        is_succeed = False
        message = update.message.text
        if i == 0:
            reply_message = await update.message.reply_text(text="Bing is typing...")

        try:
            prev_time = time.time()
            prev_reply_text = ""
            async for is_done, res in bot.get_reply_stream(message):
                if is_done:
                    reply_text, inline_keyboard = await handle_bing_reply(res)
                    is_succeed = True
                    if reply_text.strip() != prev_reply_text.strip() or inline_keyboard:
                        try:
                            await reply_message.edit_text(
                                text=reply_text,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=InlineKeyboardMarkup(inline_keyboard),
                            )
                        except Exception:
                            try:
                                await reply_message.edit_text(
                                    text="[Default ParseMode]\n" + reply_text
                                )
                            except Exception as err:
                                is_succeed = False
                                await reset_reply(
                                    reply_message.edit_text
                                    + "\nRetrying(%s)..." % (i + 1)
                                )
                else:
                    if time.time() - prev_time > message_update_time and res:
                        prev_time = time.time()
                        prev_reply_text = res
                        await reply_message.edit_text(
                            text=res,
                        )
        except Exception as err:
            await reset_reply(
                reply_message.edit_text, str(err) + "\nRetrying(%s)..." % (i + 1)
            )
        if is_succeed:
            break


@check_user_id
async def creative(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_style
    conversation_style = "creative"
    await update.message.reply_text(
        text="Conversation style is %s." % conversation_style
    )


@check_user_id
async def balanced(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_style
    conversation_style = "balanced"
    await update.message.reply_text(
        text="Conversation style is %s." % conversation_style
    )


@check_user_id
async def precise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global conversation_style
    conversation_style = "precise"
    await update.message.reply_text(
        text="Conversation style is %s." % conversation_style
    )


@check_user_id
async def set_cookies_by_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = await context.bot.get_file(update.message.document)
        bytearray_content = await file.download_as_bytearray()
        cookies = json.loads(bytearray_content.decode("utf-8"))
        await bot.bot_set_cookies(cookies)
        await update.message.reply_text(text="Cookies set successfully.")
    except Exception as err:
        await update.message.reply_text(
            text="Failed to set cookies.\nPlease make sure you upload the correct cookies file.\nError: %s"
            % str(err)
        )


if __name__ == "__main__":
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("creative", creative))
    application.add_handler(CommandHandler("balanced", balanced))
    application.add_handler(CommandHandler("precise", precise))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    # document
    application.add_handler(
        MessageHandler(filters.Document.ALL, set_cookies_by_document)
    )

    application.run_polling()
