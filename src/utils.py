import httpx
from pyrogram.types import CallbackQuery, Message
from pyrogram.enums import ChatAction

from src import const


http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0),
    follow_redirects=True
)


async def http_request(
        url: str,
        msg: Message | None = None,
        query: CallbackQuery | None = None,
        page: str | None = None
) -> httpx.Response | None:
    assert (msg is None) != (query is None)
    if msg:
        await msg.reply_chat_action(ChatAction.TYPING)
    response = await http_client.get(
        url,
        params={'page': page} if page else None,
    )
    if response.status_code == httpx.codes.OK:
        return response
    if msg:
        await msg.reply(text=const.BAD_REQUEST_MSG)
    elif query:
        await query.answer(
            text=const.BAD_REQUEST_MSG,
            cache_time=const.ERROR_CACHE_TIME
        )


def optimize_text(text: str) -> str:
    """
    Сокращение текста путём замены некоторых символов.
    """
    ordinary_replacement_sequences = {'...': '…', ' – ': ' — '}
    cyclic_replacement_sequences = {'  ': ' ', '\n ': '\n', '\n\n\n': '\n\n'}
    text = text.strip()
    for old_seq, new_seq in ordinary_replacement_sequences.items():
        text = text.replace(old_seq, new_seq)
    for old_seq, new_seq in cyclic_replacement_sequences.items():
        while old_seq in text:
            text = text.replace(old_seq, new_seq)
    return text


def trim_text(text: str, length: int) -> str:
    """
    Обрезка текста до нужного количества символов с добавлением троеточия в конец.
    """
    if len(text) > length:
        text = text[:length - 1].rstrip() + '…'
    return text


# def benchmark(func, repeat=1, middle=True):
#     """
#     Измеряет время выполнения функции repeat раз по среднему или суммарному времени.
#     Вероятно, колхоз.
#     """
#     times = []
#     for _ in range(repeat):
#         start = datetime.now()
#         result = func()
#         end = datetime.now()
#         times.append(end - start)
#     sum_ = 0
#     for time in times:
#         sum_ += time.microseconds
#     if middle:
#         sum_ /= len(times)
#     print(func.__name__, 'executed in', sum_, 'mcs.')
#     return result
