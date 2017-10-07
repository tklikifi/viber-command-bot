"""
Viber bot cache with Redis
"""

import datetime
import pickle
import redis
import redis.exceptions
from viber_command_bot.viber import config


class CacheError(Exception):
    pass


class Cache(object):
    """
    Class for the cache
    """

    def __init__(self):
        self.redis = redis.StrictRedis()
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

    def subscribe(self, user_id, name):
        """
        User is subscribed to the cache.

        :param user_id: Viber bot unique user id
        :param name: user name
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        self.redis.set('viber-user-id:{}'.format(user_id), name)
        self.publish('Subscribe "{}": {}'.format(name, user_id), name=name)

    def started(self, user_id, name):
        """
        User conversation is started.

        :param user_id: Viber bot unique user id
        :param name: user name
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        self.redis.set('viber-user-id:{}'.format(user_id), name)
        self.publish('Conversation started: {}'.format(user_id), name=name)

    def refresh(self, user_id, name):
        """
        User is refreshed in the cache.

        :param user_id: Viber bot unique user id
        :param name: user name
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        self.redis.set('viber-user-id:{}'.format(user_id), name)

    def unsubscribe(self, user_id):
        """
        User is un-subscribed from the cache.

        :param user_id: Viber bot unique user id
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        name = self.redis.get('viber-user-id:{}'.format(user_id)).decode()
        self.redis.delete('viber-user-id:{}'.format(user_id))
        self.publish('Un-subscribe "{}": {}'.format(name, user_id), name=name)

    def publish(self, text, media=None, name=None):
        """
        Message is published to the cache.

        :param text: message text
        :param media: media URL
        :param name: name of the user who sends the message
        :return: None
        """
        if self.redis is None or self.channel is None:
            return
        if name is None:
            name = self.name
        message = pickle.dumps({'text': text, 'media': media, 'name': name,
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
            message = self.pubsub.get_message()
        except Exception as e:
            raise CacheError('Could not get message from cache: {}'.format(e))
        if message:
            return pickle.loads(message.get('data', dict()))
        return dict()


cache = Cache()
