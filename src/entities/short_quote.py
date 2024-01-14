from functools import cached_property

from selectolax.lexbor import LexborNode

from src import utils
from src.entities.quote import Quote, QuoteTypes


class ShortQuote(Quote):
    MAX_LENGTH = 250

    def __init__(self, article_tag: LexborNode):
        self._quote_with_meta_tag = article_tag
        self._quote_tag = article_tag.css_first('div.node__content')

    @property
    def _series(self) -> None:
        return None

    @property
    def _text(self) -> str:
        text_tags = self._quote_tag.css('div.field-name-body')
        text_parts = []
        for text_tag in text_tags:
            text_parts.append(text_tag.text().strip())
        return '\n'.join(text_parts)

    @cached_property
    def header(self) -> str | None:
        match self.type:
            case QuoteTypes.pritcha:
                return f'Притча «{self._quote_tag.css_first("h2").text()}»'
            case QuoteTypes.po:
                for taxonomy_elem in self._taxonomy:
                    if taxonomy_elem.title == 'Фольклор':
                        return taxonomy_elem.plain_text
            case QuoteTypes.quote:
                authors = source = characters = None
                for taxonomy_elem in self._taxonomy:
                    match taxonomy_elem.title:
                        case 'Эпизод':
                            continue
                        case 'Цитируемые персонажи':
                            characters = 'Персонаж'
                            if taxonomy_elem.count > 1:
                                characters += 'и'
                            characters += f' {taxonomy_elem.plain_text}'
                        case 'Автор' | 'Исполнители':
                            authors = taxonomy_elem.plain_text
                            if authors == 'неизвестен':
                                authors = 'Неизвестный автор'
                        case 'Песня':
                            source = taxonomy_elem.plain_text
                        case _:
                            source = f'{taxonomy_elem.title.lower()} «{taxonomy_elem.plain_text}»'
                if authors and source:
                    return f'{authors} — {source}'
                elif source:
                    return f'{source[0].upper()}{source[1:]}'
                elif authors:
                    return authors
                elif characters:
                    return characters
                else:
                    return None

    def __str__(self):
        text = self._text
        if self.header:
            text = f'**{self.header}**\n{text}'
        text = utils.optimize_text(text)
        return utils.trim_text(text, ShortQuote.MAX_LENGTH)
