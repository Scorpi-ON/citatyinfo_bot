import httpx
from pyrogram.enums import ChatAction
from pyrogram.types import Message, CallbackQuery

import const
from ..http_client import http_client


async def http_request(
        url: str,
        message: Message = None,
        callback_query: CallbackQuery = None,
        page: str = None
) -> httpx.Response | None:
    assert not (message and callback_query)
    if message:
        await message.reply_chat_action(ChatAction.TYPING)
    try:
        url = httpx.URL(url)
    except httpx.InvalidURL:
        if message:
            await message.reply(text=const.BAD_REQUEST_MSG)
        elif callback_query:
            await callback_query.answer(
                text=const.BAD_REQUEST_MSG,
                cache_time=const.ERROR_CACHE_TIME
            )
        return
    response = await http_client.get(
        url=url,
        params={'page': page} if page else None,
    )
    if response.status_code == httpx.codes.OK:
        return response
    if message:
        await message.reply(text=const.BAD_REQUEST_MSG)
    elif callback_query:
        await callback_query.answer(
            text=const.BAD_REQUEST_MSG,
            cache_time=const.ERROR_CACHE_TIME
        )
