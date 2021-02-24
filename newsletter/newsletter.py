#!/usr/bin/env python

import imaplib
import email
import re
import os
import json
import click


CONFIG_FILEPATH = f"{os.path.dirname(os.path.realpath(__file__))}/config.json"


class Config():
    """This holds the user's configuration, or any exception that occurred while
    loading or reading it."""
    def __init__(self, host=None, user=None, password=None, error=None):
        self.host = host
        self.user = user
        self.password = password
        self.error = error

@click.group()
@click.pass_context
def cli(ctx):
    """This is a CLI tool for managing a basic newsletter."""
    try:
        with open(CONFIG_FILEPATH, 'r') as config_file:
            config = json.load(config_file)
            assert config
            ctx.obj = Config(config['host'], config['user'], config['password'])
    except (json.decoder.JSONDecodeError,
            KeyError,
            TypeError,
            AssertionError,
            FileNotFoundError) as error:
        ctx.obj = Config(error=error)


def sync_subscribers(config: Config) -> list[str]:
    """Fetch emails and return list of subscribers."""

    imap_server = imaplib.IMAP4_SSL(host=config.host)
    imap_server.login(config.user, config.password)
    imap_server.select()

    click.echo(f"Fetching emails for {config.user} at {config.host}")

    search_response, message_numbers_raw = imap_server.search(None, 'ALL')
    message_numbers = message_numbers_raw[0].split()

    if not search_response == 'OK':
        click.echo(f"Received error searching emails: {search_response}")
        return []

    subscribers = []

    for message_number in message_numbers:
        msg_response, msg_raw = imap_server.fetch(message_number, '(RFC822)')
        msg = email.message_from_bytes(msg_raw[0][1])
        if not msg_response == 'OK':
            click.echo(f"Got error reading email: {msg_response}")
            break

        sender = msg['from']
        subject = msg['subject']

        email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        email_regex_result = re.search(email_regex, sender)

        if not email_regex_result:
            click.echo(f"Couldn't parse email in {sender}")
            break

        sender_email = email_regex_result.group()
        if 'unsubscribe' in subject.lower() and sender_email in subscribers:
            click.echo(f"unsubscribe {sender}")
            subscribers.remove(sender_email)
        elif 'subscribe' in subject.lower() and not sender_email in subscribers:
            click.echo(f"subscribe {sender}")
            subscribers.append(sender_email)

    return subscribers

@cli.command()
def configure():
    """Edit the emailing config file."""

    try:
        with open(CONFIG_FILEPATH, 'r') as config_file:
            config = json.dumps(json.load(config_file), ensure_ascii=False)
            assert config
    except (AssertionError, FileNotFoundError, json.decoder.JSONDecodeError):
        click.echo("Couldn't find/read config file; creating new one ...")
        config = """{
    "host": "mail.myhost.net",
    "user": "mail@mydomain.net",
    "password": "replaceme"
}"""

    edited_config = click.edit(config)

    if not edited_config:
        click.echo("Left the config file as it was")
        return

    with open(CONFIG_FILEPATH, 'w') as config_file:
        json.dump(json.loads(edited_config), config_file)
        click.echo("Config file saved")


def ensure_config(config):
    """Checks that the given config object is valid; otherwise, raises an
    exception."""
    if config.error in [AssertionError, FileNotFoundError]:
        raise click.UsageError(
            "Couldn't find config file (use \"nwsl configure\" to create one)"
        )
    if config.error in [json.decoder.JSONDecodeError, KeyError, TypeError]:
        raise click.UsageError(
            "Couldn't read config file (use \"nwsl configure\" to change it)"
        )
    if not config.host or not config.user or not config.password:
        raise click.UsageError(
            "Config file contains empty value(s) (use \"nwsl configure\" to change it)",
        )

@cli.command()
@click.argument('filepath')
@click.pass_obj
def send_email(config, filepath):
    """Sends email at given path to all subscribers."""
    ensure_config(config)

    subscribers = sync_subscribers(config)
    click.echo(subscribers)
    click.echo(f"Sent {filepath} to {len(subscribers)} subscriber(s)")
