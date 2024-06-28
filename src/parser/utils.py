def optimize_text(text: str) -> str:
    """
    Сокращение текста путём замены некоторых символов.
    """
    cyclic_replacement_sequences = {'  ': ' ', '\n\n\n': '\n\n'}
    ordinary_replacement_sequences = {'...': '…', ' – ': ' — ', '**': '@@', '@*': '@@', '\n ': '\n'}
    text = text.strip()
    for old_seq, new_seq in cyclic_replacement_sequences.items():
        while old_seq in text:
            text = text.replace(old_seq, new_seq)
    for old_seq, new_seq in ordinary_replacement_sequences.items():
        text = text.replace(old_seq, new_seq)
    return text


def trim_text(text: str, length: int) -> str:
    """
    Обрезка текста до нужного количества символов с добавлением троеточия в конец.
    """
    if len(text) > length:
        text = text[:length - 1].rstrip() + '…'
    return text
