import httpx
from pyrogram.types import CallbackQuery, Message
from pyrogram.enums import ChatAction

import const


http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0),
    follow_redirects=True
)


async def http_request(
        url: str,
        message: Message | None = None,
        callback_query: CallbackQuery | None = None,
        page: str | None = None
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


def optimize_text(text: str) -> str:
    """
    Сокращение текста путём замены некоторых символов.
    """
    cyclic_replacement_sequences = {'  ': ' ', '\n\n\n': '\n\n'}
    ordinary_replacement_sequences = {'...': '…', ' – ': ' — ', '**': '@@', '@*': '@@', '\n ': '\n'}
    text = text.strip()
    for old_seq, new_seq in cyclic_replacement_sequences.items():
        while old_seq in text:
            text = text.replace(old_seq, new_seq)
    for old_seq, new_seq in ordinary_replacement_sequences.items():
        text = text.replace(old_seq, new_seq)
    return text


def trim_text(text: str, length: int) -> str:
    """
    Обрезка текста до нужного количества символов с добавлением троеточия в конец.
    """
    if len(text) > length:
        text = text[:length - 1].rstrip() + '…'
    return text
