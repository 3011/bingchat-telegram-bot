import json
from EdgeGPT import Chatbot, ConversationStyle

with open("./cookies.json", "r") as f:
    cookies = json.load(f)


bot = Chatbot(cookies=cookies)


async def reset_chat():
    await bot.reset()


async def get_reply(message, style="banlanced"):
    if style == "creative":
        conversation_style = ConversationStyle.creative
    elif style == "precise":
        conversation_style = ConversationStyle.precise
    else:
        conversation_style = ConversationStyle.balanced

    return await bot.ask(
        prompt=message,
        conversation_style=conversation_style,
    )


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
