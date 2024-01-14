import functools

from src import utils
from src.entities.base_quote import BaseQuote


class ShortQuote(BaseQuote):
    MAX_LENGTH = 250

    @functools.cached_property
    def text(self) -> str:
        text = self._text
        if isinstance(text, tuple):
            text = f'{text[0]}\n\n{text[1]}'
        return utils.trim_text(utils.optimize_text(text), ShortQuote.MAX_LENGTH)

    def __str__(self):
        text = self.text
        if self.header:
            text = f'**{self.header}**\n{text}'
        return utils.trim_text(text, ShortQuote.MAX_LENGTH)
