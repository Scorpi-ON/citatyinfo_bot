class Topic:
    def __init__(self, text: str, url: str):
        self.text = text.lower() \
                        .replace(' ', '_') \
                        .replace(',_', ' #')
        self.url = url

    def __str__(self):
        return f'[#{self.text}]({self.url})'
