#!/usr/bin/env python3

import argparse
import sys
from viber import create_text_messages, viber_config, viber
from viberbot.api.messages import URLMessage


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Send message using Viber')
    parser.add_argument('--user-id', help='user id')
    parser.add_argument('--media-url', help='media URL')
    parser.add_argument('message', help='message text')
    parser.set_defaults(user_id=viber_config['notify user id'])
    return parser.parse_args()


def main():
    args = parse_command_line_arguments()
    messages = list()
    if args.message:
        messages = create_text_messages(args.message)
    if args.media_url:
        messages.append(URLMessage(media=args.media_url))
    if messages:
        viber.send_messages(args.user_id, messages)
    return 0


if __name__ == '__main__':
    sys.exit(main())
