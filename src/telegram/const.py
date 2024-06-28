import json
from ..parser import const

MAX_ROW_BUTTON_COUNT = 8
RESULT_CACHE_TIME = 120
ERROR_CACHE_TIME = 30
MAX_CALLBACK_DATA_LENGTH = 64
MAX_CALLBACK_ANSWER_LENGTH = 200

QUOTE_SHORT_TEXT_LENGTH = 250

with open('command_templates.json', 'r') as f:
    raw_command_links = f.read()
raw_command_links = raw_command_links.format(
    BASE_URL=const.BASE_URL,
    CATEGORY_URL=const.CATEGORY_URL,
    TOP_RATING_URL=const.TOP_RATING_URL
)
MULTIPLE_COMMAND_LINKS = json.loads(raw_command_links)

BAD_REQUEST_MSG = 'Не удалось обработать данный запрос. 😔'
NOTHING_FOUND_MSG = 'По этому запросу ничего не найдено. 🤷🏻‍♂️'
