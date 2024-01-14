from src import utils
from src.entities.base_quote import BaseQuote


class ShortQuote(BaseQuote):
    MAX_LENGTH = 250

    def __str__(self):
        text = self._text
        if isinstance(text, tuple):
            text = f'{text[0]}\n\n{text[1]}'
        if self.header:
            text = f'**{self.header}**\n{text}'
        text = utils.optimize_text(text)
        return utils.trim_text(text, ShortQuote.MAX_LENGTH)
