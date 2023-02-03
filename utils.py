import zlib
import unicodedata
from datetime import datetime


def normalize(text: str) -> str:
    '''
    Исправляет неправильные unicode-символы в тексте, полученном из HTML,
    и слегка сокращает его.
    '''
    text = unicodedata.normalize('NFKC', text)
    text = text.strip() \
               .replace('...', '…') \
               .replace('\n\n\n', '\n\n') \
               .replace('\n ', '\n') \
               .replace('  ', ' ')
    return text


def compress(long_text: str) -> bytes:
    '''Сжатие строки в байты, которые занимают меньше памяти'''
    zlib.compress(long_text.encode('utf-8'))


def decompress(binary_text: bytes) -> str:
    '''Распаковка сжатых байтов обратно в строку'''
    zlib.decompress(binary_text).decode('utf-8')


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
