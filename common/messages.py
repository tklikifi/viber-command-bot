from viberbot.api.messages.text_message import TextMessage


MAX_TEXT_MESSAGE_SIZE = 7 * 1000  # 7K limit in Viber API
NUMBER_OF_TEXT_MESSAGES = 20


def create_text_message_list(text):
    """
    Split text into a list of text messages. Also, lLimit the number of the
    text messages.
    """
    messages = list()
    if not text:
        return messages
    truncated_text = text[:(NUMBER_OF_TEXT_MESSAGES * MAX_TEXT_MESSAGE_SIZE)]
    for chunk in [truncated_text[i:i + MAX_TEXT_MESSAGE_SIZE] for i in range(
            0, len(truncated_text), MAX_TEXT_MESSAGE_SIZE)]:
        messages.append(TextMessage(text=chunk))
    if truncated_text != text:
        messages.append(TextMessage(text='<truncated>'))
    return messages
