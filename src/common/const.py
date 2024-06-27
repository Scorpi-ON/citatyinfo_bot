import re

# Общее
STR_ENCODING = 'UTF-8'

# Telegram
MAX_ROW_BUTTON_COUNT = 8
RESULT_CACHE_TIME = 120
ERROR_CACHE_TIME = 30
MAX_CALLBACK_DATA_LENGTH = 64
MAX_CALLBACK_ANSWER_LENGTH = 200

# Строки, использующиеся в нескольких местах
BAD_REQUEST_MSG = 'Не удалось обработать данный запрос. 😔'
NOTHING_FOUND_MSG = 'По этому запросу ничего не найдено. 🤷🏻‍♂️'

# Ссылки
BASE_URL = 'https://citaty.info/%s'
CATEGORY_URL = BASE_URL % '%s/quotes'
SEARCH_URL = BASE_URL % 'search/site/%s'
TOP_RATING_URL = BASE_URL % 'rating/%s'
QUOTE_URL = BASE_URL % 'quote/%s'
AJAX_URL = BASE_URL % 'ajax/en_body/%s'
RANDOM_URL = BASE_URL % 'random'

# Регулярки
QUOTE_PATTERN = re.compile(
    r'^https://citaty.info/(?:random|(?:quote|po|proverb|pritcha|parable)/(\d+)(?:#comment(?:-form|s))?)$'
)
ORIGINAL_CALLBACK_PATTERN = re.compile(r'o(\d+)')
EXPLANATION_CALLBACK_PATTERN = re.compile(r'e(?:quote|po|pritcha|parable)/\d+')
GET_QUOTE_CALLBACK_PATTERN = re.compile(r'(?:quote|po|pritcha|parable)/\d+')
PAGE_PATTERN = re.compile(r'p(\d+)')

COMMON_URL_PATTERN = re.compile(r'^https://citaty\.info/.+')

# Команды
MULTIPLE_QUOTES_COMMANDS = {
    'top': TOP_RATING_URL % 'best',
    'top_month': TOP_RATING_URL % 'best/month',
    'top_week': TOP_RATING_URL % 'best/week',
    'short': BASE_URL % 'short',
    'english': CATEGORY_URL % 'english',
    'pictures': BASE_URL % 'pictures',
    'author': CATEGORY_URL % 'man',
    'unknown': BASE_URL % 'other',
    'book': CATEGORY_URL % 'book',
    'movie': CATEGORY_URL % 'movie',
    'series': CATEGORY_URL % 'series',
    'tv': CATEGORY_URL % 'tv',
    'cartoon': CATEGORY_URL % 'cartoon',
    'anime': CATEGORY_URL % 'anime',
    'music': CATEGORY_URL % 'music',
    'game': CATEGORY_URL % 'game',
    'theater': CATEGORY_URL % 'theater',
    'poetry': CATEGORY_URL % 'poetry',
    'comics': CATEGORY_URL % 'comics',
    'samizdat': CATEGORY_URL % 'self',
    'proverb': BASE_URL % 'po/quotes',
    'parable': BASE_URL % 'pritchi',
    'antitop': TOP_RATING_URL % 'worst'
}
