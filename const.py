import re

# Telegram
RESULT_CACHE_TIME = 120
ERROR_CACHE_TIME = 30
MAX_CALLBACK_DATA_LENGTH = 128
MAX_CALLBACK_ANSWER_LENGTH = 200
BAD_REQUEST_MSG = 'Не удалось выполнить запрос, возможно ссылка некорректна!' \
                  ' Если же она открывается в браузере, попытку позже.'

# Ссылки
BASE_URL = 'https://citaty.info/%s'
CATEGORY_URL = BASE_URL % '%s/quotes'
SEARCH_URL = BASE_URL % 'search/site/%s'
TOP_RATING_URL = BASE_URL % 'rating/%s'
QUOTE_URL = BASE_URL % 'quote/%s'
PRITCHA_URL = BASE_URL % 'pritcha/%s'
PO_URL = BASE_URL % 'po/%s/quotes'
AJAX_URL = BASE_URL % 'ajax/en_body/%s'
RANDOM_URL = BASE_URL % 'random'

# Регулярки
QUOTE_PATTERN = re.compile(
    r'^https://citaty.info/(?:quote|pritcha|po|proverb)/(\d+)(?:#comment(?:-form|s))?$'
)
ORIGINAL_CALLBACK_PATTERN = re.compile(r'o(\d+)')
EXPLANATION_CALLBACK_PATTERN = re.compile(r'e(?:quote|po|pritcha)\/\d+')
GET_QUOTE_CALLBACK_PATTERN = re.compile(r'(?:quote|po|pritcha)\/\d+')
PAGE_PATTERN = re.compile(r'p(\d+)')

COMMON_URL_PATTERN = re.compile(r'^https:\/\/citaty\.info\/.+')

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
    'proverb': PO_URL,
    'parable': PRITCHA_URL,
    'antitop': TOP_RATING_URL % 'worst'
}

# Юзер-агенты для базового обхода блокировок сайта
# from faker import Faker
# fake = Faker()
# for _ in range(10):
#    print(fake.user_agent())
USER_AGENTS = (
    'Mozilla/5.0 (compatible; MSIE 5.0; Windows 98; Trident/4.1)',
    'Opera/9.14.(Windows 95; hy-AM) Presto/2.9.177 Version/11.00',
    'Mozilla/5.0 (compatible; MSIE 5.0; Windows NT 6.1; Trident/5.1)',
    'Mozilla/5.0 (compatible; MSIE 5.0; Windows NT 4.0; Trident/4.1)',
    'Mozilla/5.0 (Android 7.1; Mobile; rv:38.0) Gecko/38.0 Firefox/38.0',
    'Mozilla/5.0 (Android 4.4.1; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:1.9.6.20) Gecko/2016-04-03 14:58:58 Firefox/15.0',
    'Mozilla/5.0 (Windows NT 6.0; oc-FR; rv:1.9.2.20) Gecko/2013-11-14 20:34:54 Firefox/10.0',
    'Mozilla/5.0 (Windows 98; Win 9x 4.90; sid-ET; rv:1.9.2.20) Gecko/2014-07-03 15:19:24 Firefox/3.8',
    'Mozilla/5.0 (Windows NT 5.2) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/25.0.810.0 Safari/535.2',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/531.1 (KHTML, like Gecko) Chrome/32.0.817.0 Safari/531.1',
    'Mozilla/5.0 (Windows 98; Win 9x 4.90; kn-IN; rv:1.9.2.20) Gecko/2011-08-18 15:14:46 Firefox/3.6.18',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/35.0.891.0 Safari/535.1',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/531.2 (KHTML, like Gecko) Chrome/26.0.880.0 Safari/531.2',
    'Mozilla/5.0 (Macintosh; PPC Mac OS X 10 10_4 rv:2.0; cmn-TW) AppleWebKit/535.3.4 (KHTML, like Gecko) Version/5.0 Safari/535.3.4',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10 6_8 rv:3.0; st-ZA) AppleWebKit/532.43.1 (KHTML, like Gecko) Version/4.0.5 Safari/532.43.1',
    'Mozilla/5.0 (iPad; CPU iPad OS 14_2_1 like Mac OS X) AppleWebKit/531.0 (KHTML, like Gecko) CriOS/35.0.871.0 Mobile/65L777 Safari/531.0',
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10 12_3 rv:2.0; gl-ES) AppleWebKit/532.49.1 (KHTML, like Gecko) Version/5.0.4 Safari/532.49.1',
    'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_1 like Mac OS X; bho-IN) AppleWebKit/531.23.5 (KHTML, like Gecko) Version/3.0.5 Mobile/8B115 Safari/6531.23.5'
)
