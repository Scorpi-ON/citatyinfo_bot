import uvloop
import httpx
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

import const
import utils
from quote import Quote
from quotes_page import QuotesPage


uvloop.install()
app = Client('TestBot')
http_client = httpx.AsyncClient()


@app.on_message(filters.command(['start', 'help']))
async def help(_, message: Message):
    await message.reply(
        'Справка с полным описанием функционала бота пока не написана.'
        ' Но вы можете начать его использование с команд.'
        ' Также можно искать цитаты по гиперссылкам из сообщений'
        ' и по собственным текстовым запросам.'
    )


@app.on_message(filters.command('random'))
async def random(_, message: Message):
    response = await http_client.get(const.RANDOM_URL)
    if response.status_code == 200:
        quote = Quote(response.text)
        if quote.images:
            messages = await message.reply_media_group(quote.images)
            message = messages[0]
        await message.reply(
            str(quote), quote=bool(quote.images),
            reply_markup=quote.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_message(filters.command(list(const.MULTIPLE_QUOTES_COMMANDS)))
async def category_commands(_, message: Message):
    response = await http_client.get(
        const.MULTIPLE_QUOTES_COMMANDS[message.command[0]]
    )
    if response.status_code == 200:
        quotes_page = QuotesPage(response.text)
        await message.reply(
            str(quotes_page),
            quote=True,
            reply_markup=quotes_page.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_message(filters.regex(const.QUOTE_PATTERN))
async def quote_by_link(_, message: Message):
    response = await http_client.get(message.text)
    if response.status_code == 200:
        quote = Quote(response.text)
        if quote.images:
            messages = await message.reply_media_group(quote.images)
            message = messages[0]
        await message.reply(
            str(quote), quote=bool(quote.images),
            reply_markup=quote.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_message()
async def quote_search(_, message: Message):
    response = await http_client.get(const.SEARCH_URL % message.text)
    if response.status_code == 200:
        quotes_page = QuotesPage(response.text)
        await message.reply(
            str(quotes_page),
            quote=True,
            reply_markup=quotes_page.keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_callback_query(filters.regex(const.PAGE_PATTERN))
async def turn_page(_, callback_query: CallbackQuery):
    page, = const.PAGE_PATTERN.match(callback_query.data).groups()
    request_msg = callback_query.message.reply_to_message
    if request_msg.text[1:] in const.MULTIPLE_QUOTES_COMMANDS:      # почему-то в сообщениях, полученных посредством коллбэка,
        url = const.MULTIPLE_QUOTES_COMMANDS[request_msg.text[1:]]  # не работает метод command
    else:
        url = const.SEARCH_URL % request_msg.text
    response = await http_client.get(url, params={'page': page} if page != '0' else None)  # нулевую страницу сайт переваривает медленно
    if response.status_code == 200:
        quotes_page = QuotesPage(response.text)
        await callback_query.message.edit(
            str(quotes_page),
            reply_markup=quotes_page.keyboard,
            disable_web_page_preview=True
        )
    else:
        await callback_query.message.reply(
            'Ошибка подключения к сайту! Повторите попытку позже.'
        )


@app.on_callback_query(filters.regex(const.ORIGINAL_CALLBACK_PATTERN))
async def original_request(_, callback_query: CallbackQuery):
    id, = const.ORIGINAL_CALLBACK_PATTERN.match(callback_query.data).groups()
    response = await http_client.get(const.AJAX_URL % id)
    if response.status_code == 200:
        original_text = BeautifulSoup(response.json()[1]['data'], 'lxml').text
        await callback_query.answer(
            utils.normalize(original_text),
            show_alert=True,
            cache_time=const.RESULT_CACHE_TIME
        )
    else:
        await callback_query.answer(
            'Ошибка подключения к сайту! Повторите попытку позже.',
            cache_time=const.ERROR_CACHE_TIME
        )


@app.on_callback_query(filters.regex(const.EXPLANATION_CALLBACK_PATTERN))
async def explanation_request(_, callback_query: CallbackQuery):
    rel_link = callback_query.data[1:]
    response = await http_client.get(const.BASE_URL % rel_link)
    if response.status_code == 200:
        quote = Quote(response.text)
        await callback_query.answer(
            utils.cut(quote.explanation, const.MAX_CALLBACK_ANSWER_LENGTH),
            show_alert=True,
            cache_time=const.RESULT_CACHE_TIME
        )
    else:
        await callback_query.answer(
            'Ошибка подключения к сайту! Повторите попытку позже.',
            cache_time=const.ERROR_CACHE_TIME
        )


@app.on_callback_query(filters.regex(const.GET_QUOTE_CALLBACK_PATTERN))
async def quote_by_callback(_, callback_query: CallbackQuery):
    response = await http_client.get(const.BASE_URL % callback_query.data)
    if response.status_code == 200:
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
    else:
        await app.send_message(
            callback_query.from_user.id,
            'Ошибка подключения к сайту! Повторите попытку позже.'
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
