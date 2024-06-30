import json
from ..parser import const

MAX_ROW_BUTTON_COUNT = 8
RESULT_CACHE_TIME = 120
ERROR_CACHE_TIME = 30
MAX_CALLBACK_DATA_LENGTH = 64
MAX_CALLBACK_ANSWER_LENGTH = 200

QUOTE_SHORT_TEXT_LENGTH = 250

with open('src/telegram/data/command_templates.json', encoding=const.STR_ENCODING) as f:
    MULTIPLE_COMMAND_LINKS: dict = json.load(f)
for key, value in MULTIPLE_COMMAND_LINKS.items():
    MULTIPLE_COMMAND_LINKS[key] = const.BASE_URL % value

BAD_REQUEST_MSG = 'Не удалось обработать данный запрос. 😔'
NOTHING_FOUND_MSG = 'По этому запросу ничего не найдено. 🤷🏻‍♂️'
