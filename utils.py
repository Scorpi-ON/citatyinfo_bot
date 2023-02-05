import zlib
from datetime import datetime

from pyrogram import filters
from pyrogram.types import CallbackQuery


async def str_query_filter(_, __, callback_query: CallbackQuery) -> bool:
    return isinstance(callback_query.data, str)


str_query_filter = filters.create(str_query_filter)


def optimize(text: str) -> str:
    '''
    Сокращает текст путём замены некоторых символов.
    '''
    text = text.strip().replace('...', '…').replace(' – ', ' — ')
    for pair in (('  ', ' '), ('\n ', '\n'), ('\n\n\n', '\n\n')):  # для этих последовательностей
        while pair[0] in text:                                     # cимволов нужна циклическая замена
            text = text.replace(*pair)
    return text


def compress(long_text: str) -> bytes:
    '''Сжатие строки в байты, которые занимают меньше памяти'''
    return zlib.compress(long_text.encode('utf-8'), 9)


def decompress(binary_text: bytes) -> str:
    '''Распаковка сжатых байтов обратно в строку'''
    return zlib.decompress(binary_text).decode('utf-8')


def cut(text: str, char_count: int) -> str:
    '''
    Обрезает текст до нужного количества символов с добавлением троеточия в конец.
    '''
    if len(text) > char_count:
        text = text[:char_count - 1].rstrip() + '…'
    return text


def benchmark(func, repeat=1, middle=True):
    '''
    Измеряет время выполнения функции repeat раз по среднему или суммарному времени.
    '''
    times = []
    for _ in range(repeat):
        start = datetime.now()
        result = func()
        end = datetime.now()
        times.append(end - start)
    sum = 0
    for time in times:
        sum += time.microseconds
    if middle:
        sum /= len(times)
    print(func.__name__, 'executed in', sum, 'mcs.')
    return result
