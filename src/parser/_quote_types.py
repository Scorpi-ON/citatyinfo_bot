import enum


class QuoteTypes(enum.Enum):
    """
    Типы цитат, использующиеся в ссылках на них.
    Examples:
        ``quote``: обычная цитата — https://citaty.info/quote/35045

        ``po``: пословица / поговорка — https://citaty.info/po/247673
        (подходят также цитаты вида https://citaty.info/proverb/110707, если вместо ``proverb`` использовать ``po``)

        ``patch``: притча — https://citaty.info/pritcha/121736
    """
    quote = 0
    po = 1
    pritcha = 2
