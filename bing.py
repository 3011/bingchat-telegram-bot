import asyncio
from EdgeGPT import Chatbot, ConversationStyle


async def bot_init():
    return await Chatbot.create()


bot = asyncio.run(bot_init())
asyncio.set_event_loop(asyncio.new_event_loop())


async def bot_set_cookies(cookies):
    new_bot = await Chatbot.create(cookies=cookies)
    global bot
    del bot
    bot = new_bot


async def reset_chat():
    await bot.reset()


async def get_reply_stream(message, style="banlanced"):
    if style == "creative":
        conversation_style = ConversationStyle.creative
    elif style == "precise":
        conversation_style = ConversationStyle.precise
    else:
        conversation_style = ConversationStyle.balanced

    async for res in bot.ask_stream(
        prompt=message,
        conversation_style=conversation_style,
    ):
        yield res
