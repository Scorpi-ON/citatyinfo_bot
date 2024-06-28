from pyrogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

from .. import const as tg_const
from src.parser import Quote, TaxonomyElem
from src.parser import const as parser_const


class TgQuoteFormatter:
    def __init__(self, quote: Quote):
        self._quote = quote

    @staticmethod
    def _format_taxonomy_elem(elem: TaxonomyElem) -> str:
        text = f'{elem.emoji} **{elem.title}:** '
        for content_item in elem.content:
            if isinstance(content_item, dict):
                text += f'[{content_item["text"]}]({content_item["url"]}), '
            else:
                text += f'{content_item}, '
        return text.removesuffix(', ')

    @property
    def text(self) -> str:
        text = self._quote.text
        if isinstance(text, tuple):
            text = f'**Оригинал:**\n{text[0]}\n\n**Перевод:**\n{text[1]}'
        text += '\n\n'
        text += '\n'.join(
            self._format_taxonomy_elem(taxonomy_elem)
            for taxonomy_elem in self._quote.taxonomy
        )
        text += '\n\n'
        text += ' '.join(
            f'[{topic.text}]({topic.url})' for topic in self._quote.topics
        )
        return text

    @property
    def media(self) -> list[InputMediaPhoto]:
        return [InputMediaPhoto(url) for url in self._quote.image_links]

    @property
    def reply_markup(self) -> InlineKeyboardMarkup:
        row = []
        if self._quote.explanation:
            explanation = self._quote.explanation.encode(parser_const.STR_ENCODING)
            if len(explanation) > tg_const.MAX_CALLBACK_DATA_LENGTH:
                explanation = f'e{self._quote.rel_link}'
            row.append({'text': '🔮 Пояснение', 'callback_data': explanation})
        if self._quote.has_original:
            row.append({'text': '🇬🇧 Оригинал', 'callback_data': f'o{self._quote.id}'})
        row.append({'text': '🔗 Открыть', 'url': parser_const.BASE_URL % self._quote.rel_link})
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(**button_data) for button_data in row]
        ])
