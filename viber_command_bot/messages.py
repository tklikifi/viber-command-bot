"""
Utility functions for Viber bot messages
"""

from viber_command_bot.cache import cache
from viber_command_bot.config import config
from viber_command_bot.viber import viber
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


def send_message(user_id, text, media=None):
    """
    Send text message.

    :param user_id: viber user id who will receive the message
    :param text: text to send
    :param media: URL to media file
    :return: None
    :raises Exception: if message sending fails
    """
    if not config.getboolean('Viber', 'command_executor', fallback=False):
        # External command executor daemon is not used.
        # Publish the answer message.
        cache.publish(user_id, text, media=media)
    messages = create_text_message_list(text)
    if media is not None:
        messages.append(URLMessage(media=media))
    viber.send_messages(user_id, messages)
