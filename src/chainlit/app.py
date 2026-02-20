import chainlit as cl
from src.chainlit.config import chainlit_settings
from src.chainlit.handlers import ChainlitHandlers


_handlers = ChainlitHandlers(chainlit_settings)


@cl.set_starters
async def set_starters() -> list[cl.Starter]:
    return await _handlers.set_starters()


@cl.on_chat_start
async def on_chat_start() -> None:
    await _handlers.on_chat_start()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    await _handlers.on_message(message)
