import asyncio

import httpx
from pyrogram.enums import ChatAction
from pyrogram.types import Message, CallbackQuery

from ..http_client import http_client
from ..parser import Quote, QuotePage, QuoteTypes
from ..parser import const as parser_const
from . import const as tg_const


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
            await message.reply(text=tg_const.BAD_REQUEST_MSG)
        elif callback_query:
            await callback_query.answer(
                text=tg_const.BAD_REQUEST_MSG,
                cache_time=tg_const.ERROR_CACHE_TIME
            )
        return
    response = await http_client.get(
        url=url,
        params={'page': page} if page else None,
    )
    if response.status_code == httpx.codes.OK:
        return response
    if message:
        await message.reply(text=tg_const.BAD_REQUEST_MSG)
    elif callback_query:
        await callback_query.answer(
            text=tg_const.BAD_REQUEST_MSG,
            cache_time=tg_const.ERROR_CACHE_TIME
        )


async def refresh_page_quotes(quote_page: QuotePage, page: str):
    response_tasks = {}
    async with asyncio.TaskGroup() as tg:
        for num, quote in enumerate(quote_page.quotes):
            if quote.type is QuoteTypes.quote:
                response_tasks[num] = tg.create_task(http_request(
                    url=parser_const.BASE_URL % quote.rel_link,
                    page=page if page != '0' else None
                ))
    for num, response_task in response_tasks.items():
        quote_page.quotes[num] = Quote(
            html_page=response_task.result().text
        )
