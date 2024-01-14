import typing
import functools

from selectolax.lexbor import LexborHTMLParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src import utils, const
from src.entities.base_quote import BaseQuote


class Quote(BaseQuote):
    """
    Одиночная цитата.
    """

    def __init__(self, html_page: str):
        """
        Args:
            html_page: веб-страница, содержащая цитату
        """
        self._tree = LexborHTMLParser(html_page).body
        self._quote_with_meta_tag = self._tree.css_first('article')
        super().__init__(self._quote_with_meta_tag)

    @property
    def _pritcha_header(self) -> str:
        """
        Заголовок притчи.
        """
        header_tag = self._tree.css_first('h1')
        if header_tag is None:                            # У случайных притч хедер находится
            return super()._pritcha_header  # непосредственно перед текстом
        return header_tag.text()

    @functools.cached_property
    def _string_representation(self) -> str:
        text = self._text
        topics = tuple(self._topics)
        if isinstance(text, tuple):
            text = f'**Оригинал:**\n{text[0]}\n\n**Перевод:**\n{text[1]}'
        text += '\n\n'
        for taxonomy_elem in self._taxonomy:
            text += f'{taxonomy_elem}\n'
        text += '\n'
        for topic in topics:
            text += f'[#{topic["text"]}]({topic["url"]}) '
        return utils.optimize_text(text)

    def __str__(self):
        return self._string_representation

    @functools.cached_property
    def keyboard(self) -> InlineKeyboardMarkup:
        row = []
        # if rating := self.rating:
        #     first_row.append(InlineKeyboardButton('⭐ Рейтинг', rating))
        if explanation := self.explanation:
            explanation = explanation.encode(const.STR_ENCODING)
            if len(explanation) > const.MAX_CALLBACK_DATA_LENGTH:
                explanation = f'e{self.rel_link}'
            row.append(InlineKeyboardButton('🔮 Пояснение', explanation))
        if self.has_original:
            row.append(InlineKeyboardButton('🇬🇧 Оригинал', f'o{self.id}'))
        row.append(InlineKeyboardButton('🔗 Открыть', url=const.BASE_URL % self.rel_link))
        return InlineKeyboardMarkup([row])
