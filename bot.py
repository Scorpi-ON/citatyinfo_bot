import uvloop
import httpx
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ChatAction

import const
import utils
from quote import Quote
from quotes_page import QuotesPage


uvloop.install()
app = Client('TestBot')
http_client = httpx.AsyncClient()


async def request(
        url: str,
        message: Message | None = None,
        callback_query: CallbackQuery | None = None,
        page: str | None = None
) -> httpx.Response | None:
    assert bool(message) != bool(callback_query)
    if message:
        await message.reply_chat_action(ChatAction.TYPING)
    response = await http_client.get(
        url, follow_redirects=True,
        params={'page': page} if page else None
    )
    if response.status_code == 200:
        return response
    else:
        if message:
            await message.reply(const.BAD_REQUEST_MSG)
        else:
            await callback_query.answer(
                const.BAD_REQUEST_MSG,
                cache_time=const.ERROR_CACHE_TIME
            )


@app.on_message(filters.command(['start', 'help']))
async def help(_, message: Message):
    await message.reply(
        'Справка с полным описанием функционала бота пока не написана.'
        ' Но вы можете начать его использование с команд.'
        ' Также можно искать цитаты по гиперссылкам из сообщений'
        ' и по собственным текстовым запросам.'
    )


@app.on_message(
    filters.command('random')
    | filters.regex(const.QUOTE_PATTERN)
)
async def single_quote(_, message: Message):
    if message.command:
        url = const.RANDOM_URL
    else:
        url = message.text
    if response := await request(url, message):
        quote = Quote(response.text)
        if quote.images:
            messages = await message.reply_media_group(quote.images)
            message = messages[0]
        await message.reply(
            str(quote), quote=bool(quote.images),
            reply_markup=quote.keyboard,
            disable_web_page_preview=True
        )


@app.on_message(
    filters.command(list(const.MULTIPLE_QUOTES_COMMANDS))
    | filters.text
)
async def multiple_quotes(_, message: Message):
    if message.command:
        url = const.MULTIPLE_QUOTES_COMMANDS[message.command[0]]
    elif const.COMMON_URL_PATTERN.match(message.text):
        url = message.text
    else:
        url = const.SEARCH_URL % message.text
    if response := await request(url, message):
        quotes_page = QuotesPage(response.text)
        await message.reply(
            str(quotes_page),
            quote=True,
            reply_markup=quotes_page.keyboard,
            disable_web_page_preview=True
        )


@app.on_callback_query(
    utils.str_callback_filter
    & filters.regex(const.PAGE_PATTERN)
)
async def turn_page(_, callback_query: CallbackQuery):
    page, = const.PAGE_PATTERN.match(callback_query.data).groups()
    request_msg = callback_query.message.reply_to_message
    if request_msg.text[1:] in const.MULTIPLE_QUOTES_COMMANDS:      # в сообщениях, полученных не по фильтру
        url = const.MULTIPLE_QUOTES_COMMANDS[request_msg.text[1:]]  # команд, не работает метод command
    elif const.COMMON_URL_PATTERN.match(request_msg.text):
        url = request_msg.text
    else:
        url = const.SEARCH_URL % request_msg.text
    if response := await request(url, callback_query=callback_query, page=page):
        quotes_page = QuotesPage(response.text)
        await callback_query.message.edit(
            str(quotes_page),
            reply_markup=quotes_page.keyboard,
            disable_web_page_preview=True
        )


@app.on_callback_query(
    utils.str_callback_filter
    & filters.regex(const.ORIGINAL_CALLBACK_PATTERN)
)
async def original_request(_, callback_query: CallbackQuery):
    id, = const.ORIGINAL_CALLBACK_PATTERN.match(callback_query.data).groups()
    if response := await request(const.AJAX_URL % id, callback_query=callback_query):
        soup = BeautifulSoup(response.json()[1]['data'], 'lxml')
        original_text = utils.optimize(soup.text)
        await callback_query.answer(
            utils.cut(original_text, const.MAX_CALLBACK_ANSWER_LENGTH),
            show_alert=True,
            cache_time=const.RESULT_CACHE_TIME
        )


@app.on_callback_query(
    utils.str_callback_filter
    & filters.regex(const.EXPLANATION_CALLBACK_PATTERN)
)
async def explanation_request(_, callback_query: CallbackQuery):
    rel_link = callback_query.data[1:]
    if response := await request(const.BASE_URL % rel_link, callback_query=callback_query):
        quote = Quote(response.text)
        await callback_query.answer(
            utils.cut(quote.explanation, const.MAX_CALLBACK_ANSWER_LENGTH),
            show_alert=True,
            cache_time=const.RESULT_CACHE_TIME
        )


@app.on_callback_query(
    utils.str_callback_filter
    & filters.regex(const.GET_QUOTE_CALLBACK_PATTERN)
)
async def quote_by_callback(_, callback_query: CallbackQuery):
    if response := await request(const.BASE_URL % callback_query.data, callback_query=callback_query):
        quote = Quote(response.text)
        if quote.images:
            messages = await app.send_media_group(
                callback_query.from_user.id,
                quote.images
            )
            await messages[0].reply(
                str(quote), quote=bool(quote.images),
                reply_markup=quote.keyboard,
                disable_web_page_preview=True
            )
        else:
            await app.send_message(
                callback_query.from_user.id, str(quote),
                reply_markup=quote.keyboard,
                disable_web_page_preview=True
            )
        await callback_query.answer(cache_time=const.RESULT_CACHE_TIME)


@app.on_callback_query()
async def callback_echo(_, callback_query: CallbackQuery):
    if isinstance(callback_query.data, str):
        text = callback_query.data
        show_alert = False
    else:
        text = utils.decompress(callback_query.data)
        show_alert = True
    await callback_query.answer(
        text, show_alert,
        cache_time=const.RESULT_CACHE_TIME
    )


app.run()
