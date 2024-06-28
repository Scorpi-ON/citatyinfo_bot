import re

STR_ENCODING = 'utf-8'

BASE_URL = 'https://citaty.info/%s'
TOP_RATING_URL = BASE_URL % 'rating/%s'
CATEGORY_URL = BASE_URL % '%s/quotes'
SEARCH_URL = BASE_URL % 'search/site/%s'
QUOTE_URL = BASE_URL % 'quote/%s'
AJAX_URL = BASE_URL % 'ajax/en_body/%s'
RANDOM_URL = BASE_URL % 'random'

QUOTE_PATTERN = re.compile(
    fr'^{BASE_URL % ""}(?:random|(?:quote|po|proverb|pritcha|parable)/(\d+)(?:#comment(?:-form|s))?)$'
)
ORIGINAL_CALLBACK_PATTERN = re.compile(r'o(\d+)')
EXPLANATION_CALLBACK_PATTERN = re.compile(r'e(?:quote|po|pritcha|parable)/\d+')
GET_QUOTE_CALLBACK_PATTERN = re.compile(r'(?:quote|po|pritcha|parable)/\d+')
PAGE_PATTERN = re.compile(r'p(\d+)')

COMMON_URL_PATTERN = re.compile(r'^https://citaty\.info/.+')
