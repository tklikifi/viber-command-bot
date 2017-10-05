"""
Utility functions for Viber bot messages
"""

from viber_command_bot.viber import config, viber
from viberbot.api.messages import URLMessage
from viberbot.api.messages.text_message import TextMessage


MAX_TEXT_MESSAGE_SIZE = 7000  # Limit in Viber API
NUMBER_OF_TEXT_MESSAGES = 20
MAX_TEXT_SIZE = NUMBER_OF_TEXT_MESSAGES * MAX_TEXT_MESSAGE_SIZE


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
    truncated_text = text[:MAX_TEXT_SIZE]
    for chunk in [truncated_text[i:i + MAX_TEXT_MESSAGE_SIZE] for i in range(
            0, len(truncated_text), MAX_TEXT_MESSAGE_SIZE)]:
        messages.append(TextMessage(text=chunk))
    if truncated_text != text:
        messages.append(TextMessage(text='<truncated>'))
    return messages


def send_message(text, media=None, user_id=None):
    """
    Send text message.

    :param text: text to send
    :param media: URL to media file
    :param user_id: viber user id who will receive the message
    :return: None
    :raises Exception: if message sending fails
    """
    messages = create_text_message_list(text)
    if media is not None:
        messages.append(URLMessage(media=media))
    if user_id is None:
        user_id = config.get('Viber', 'notify_user_id')
    viber.send_messages(user_id, messages)
