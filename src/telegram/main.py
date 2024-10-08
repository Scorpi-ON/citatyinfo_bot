import sys

from dotenv import dotenv_values
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler

from .handlers import *
from . import const as tg_const
from ..parser import const as parser_const

str_query_filter = filters.create(
    lambda _, __, callback_query: isinstance(callback_query.data, str)
)

handlers = (
    MessageHandler(help_, filters.command(['start', 'help'])),
    MessageHandler(
        single_quote,
        filters.command('random')
        | filters.regex(parser_const.QUOTE_PATTERN)
    ),
    MessageHandler(
        multiple_quotes,
        filters.command(list(tg_const.MULTIPLE_COMMAND_LINKS))
        | filters.text
    ),

    CallbackQueryHandler(
        turn_page,
        str_query_filter
        & filters.regex(parser_const.PAGE_PATTERN)
    ),
    CallbackQueryHandler(
        original,
        str_query_filter
        & filters.regex(parser_const.ORIGINAL_CALLBACK_PATTERN)
    ),
    CallbackQueryHandler(
        explanation,
        str_query_filter
        & filters.regex(parser_const.EXPLANATION_CALLBACK_PATTERN)
    ),
    CallbackQueryHandler(
        quote_by_callback,
        str_query_filter
        & filters.regex(parser_const.GET_QUOTE_CALLBACK_PATTERN)
    ),
    CallbackQueryHandler(callback_echo),

    InlineQueryHandler(multiple_quotes_inline)
)

if __name__ == '__main__':
    TEST_MODE = False
    credentials = dotenv_values()
    api_id = credentials['API_ID']
    api_hash = credentials['API_HASH']
    if TEST_MODE:
        name = 'TestBot'
        bot_token = credentials['TEST_TOKEN']
    else:
        name = 'Bot'
        bot_token = credentials['TOKEN']

    if sys.platform != 'win32':
        import uvloop
        uvloop.install()

    app = Client(name, api_id, api_hash, bot_token=bot_token, test_mode=TEST_MODE)
    for handler in handlers:
        app.add_handler(handler)
    app.run()
