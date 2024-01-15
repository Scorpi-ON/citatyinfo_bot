import uvloop
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler

from src.handlers import *


str_query_filter = filters.create(
    lambda _, __, callback_query: isinstance(callback_query.data, str)
)

handlers = (
    MessageHandler(help_, filters.command(['start', 'help'])),
    MessageHandler(
        single_quote,
        filters.command('random') | filters.regex(const.QUOTE_PATTERN)
    ),
    MessageHandler(
        multiple_quotes,
        filters.command(list(const.MULTIPLE_QUOTES_COMMANDS)) | filters.text
    ),

    CallbackQueryHandler(
        turn_page,
        str_query_filter & filters.regex(const.PAGE_PATTERN)
    ),
    CallbackQueryHandler(
        original,
        str_query_filter & filters.regex(const.ORIGINAL_CALLBACK_PATTERN)
    ),
    CallbackQueryHandler(
        explanation,
        str_query_filter & filters.regex(const.EXPLANATION_CALLBACK_PATTERN)
    ),
    CallbackQueryHandler(
        quote_by_callback,
        str_query_filter & filters.regex(const.GET_QUOTE_CALLBACK_PATTERN)
    ),
    CallbackQueryHandler(callback_echo),

    InlineQueryHandler(multiple_quotes_inline)
)

uvloop.install()
app = Client('Bot')
for handler in handlers:
    app.add_handler(handler)
app.run()
