"""
Viber bot cache with Redis
"""

import datetime
import pickle
import redis
import redis.exceptions
import time
from viber_command_bot.config import config


class CacheError(Exception):
    pass


class Cache(object):
    """
    Class for the cache
    """

    def __init__(self):
        self.redis = redis.StrictRedis(
            config.get('Viber', 'redis_host', fallback='localhost'))
        self.channel = config.get('Viber', 'redis_channel', fallback=None)
        self.name = config.get('Viber', 'name')
        self.pubsub = None

    def listen(self):
        """
        The client that wants to get messages through the cache needs to
        start listening the Redis pubsub channel.

        :return: None
        :raises CacheError: if Redis channel is not configured
        """
        if not self.channel:
            raise CacheError('Redis channel is not configured')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        try:
            self.pubsub.subscribe(self.channel)
        except redis.exceptions.ConnectionError as e:
            raise CacheError('Could not subscribe to Redis channel "{}": '
                             '{}'.format(self.channel, e))

    def subscribe_user(self, user_id, name):
        """
        User is subscribed to the cache.

        :param user_id: Viber bot unique user id
        :param name: user name
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        self.redis.set('viber-user-id:{}'.format(user_id), name)
        self.publish(user_id, 'Subscribe "{}": {}'.format(name, user_id),
                     name=name)

    def conversation_started(self, user_id, name):
        """
        User conversation is started.

        :param user_id: Viber bot unique user id
        :param name: user name
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        self.redis.set('viber-user-id:{}'.format(user_id), name)
        self.publish(user_id, 'Conversation started: {}'.format(user_id),
                     name=name)

    def refresh_user(self, user_id, name):
        """
        User is refreshed in the cache.

        :param user_id: Viber bot unique user id
        :param name: user name
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        self.redis.set('viber-user-id:{}'.format(user_id), name)

    def unsubscribe_user(self, user_id):
        """
        User is un-subscribed from the cache.

        :param user_id: Viber bot unique user id
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        name = self.redis.get('viber-user-id:{}'.format(user_id)).decode()
        self.redis.delete('viber-user-id:{}'.format(user_id))
        self.publish(user_id, 'Un-subscribe "{}": {}'.format(name, user_id),
                     name=name)

    def publish(self, user_id, text, media=None, name=None,
                message_type='text', output_format='text'):
        """
        Message is published to the cache.

        :param user_id: Viber bot unique user id
        :param text: message text
        :param media: media URL
        :param name: name of the user who sends the message
        :param message_type: text | execute
        :param output_format: text | json | none
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        if name is None:
            name = self.name
        message = pickle.dumps({'user_id': user_id, 'text': text,
                                'media': media, 'name': name,
                                'message_type': message_type,
                                'output_format': output_format,
                                'date': datetime.datetime.now()})
        try:
            self.redis.publish(self.channel, message)
        except redis.exceptions.ConnectionError:
            pass

    def get_message(self):
        """
        Get the next message from the cache.

        :return: message dict
        """
        if self.redis is None or self.channel is None:
            return dict()
        try:
            message = self.pubsub.get_message(timeout=10)
        except Exception as e:
            raise CacheError('Could not get message from cache: {}'.format(e))
        if message:
            return pickle.loads(message.get('data', dict()))
        return dict()

    def add_note(self, text):
        """
        Add note to cache.

        :param text: text to be copied
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        name = int(time.time() * 1000000)
        self.redis.set('viber-note:{}'.format(name), text)

    def show_note(self, number=-1):
        """
        Show note from cache.

        :param number: note number, 0 is first, 1 is second and so on
        :return: text found in the cache, or empty string
        """
        if self.redis is None or self.channel is None:
            return ''
        notes = sorted(self.redis.scan_iter('viber-note:*'))
        try:
            text = self.redis.get(notes[number])
        except IndexError:
            return ''
        if text:
            return text.decode()
        return ''

    def show_all_notes(self):
        """
        Show all notes from cache.

        :return: dict with texts found in the cache, or empty dict
        """
        if self.redis is None or self.channel is None:
            return dict()
        texts = dict()
        for i, key in enumerate(sorted(self.redis.scan_iter(
                'viber-note:*')), start=1):
            texts[i] = self.redis.get(key).decode()
        return texts

    def remove_note(self, number=-1):
        """
        Remove note from cache.

        :param number: note number, 0 is first, 1 is second and so on
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        notes = sorted(self.redis.scan_iter('viber-note:*'))
        try:
            self.redis.delete(notes[number])
        except IndexError:
            pass

    def remove_all_notes(self):
        """
        Clear all texts from cache.

        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        for key in self.redis.scan_iter('viber-note:*'):
            self.redis.delete(key)


cache = Cache()
