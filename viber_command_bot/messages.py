"""
Utility functions for Viber bot messages
"""

from viberbot.api.messages.text_message import TextMessage


MAX_TEXT_MESSAGE_SIZE = 7000  # Limit in Viber API
NUMBER_OF_TEXT_MESSAGES = 20


def create_text_message_list(text):
    """
    Split text into a list of text messages. Also, limit the number of the
    text messages.

    :param text: original text
    :return: list of TextMessage objects
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
