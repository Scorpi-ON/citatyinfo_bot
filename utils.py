import unicodedata
from datetime import datetime


def normalize(text: str) -> str:
    '''
    Исправляет неправильные unicode-символы в тексте, полученном из HTML.
    '''
    text = unicodedata.normalize('NFKC', text).strip()
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
