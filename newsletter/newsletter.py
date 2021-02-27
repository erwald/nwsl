#!/usr/bin/env python

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import email
import imaplib
import json
import os
import re
import smtplib
import ssl

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

    click.echo(f"Got {len(subscribers)} active subscriber(s)")
    return subscribers

@cli.command()
def configure():
    """Edit the emailing config file."""

    # TODO: Split IMAP & SMTP config; remove password from config.
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

def send_email_func(config: Config,
                    html_text: Optional[str],
                    plain_text: Optional[str],
                    subject: str,
                    subscribers: list[str],
                    dry_run: bool):
    def find_title_in_html(html: str) -> Optional[str]:
        result = re.search(r"<h1>(.+)<\/h1>", html)
        return result.group(1) if result else None

    def find_title_in_markdown(md: str) -> Optional[str]:
        result = re.search(r"# (.+)", md)
        return result.group(1) if result else None

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(config.host, 465, context=context) as server:
        # TODO: Get password from user input, not config file.
        server.login(config.user, config.password)

        title = find_title_in_html(html_text) if html_text else find_title_in_markdown(plain_text) or 'Untitled'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject or title
        # TODO: Add newsletter name to config.
        msg['From'] = f"Newsletter name <{config.user}>"
        # TODO: Allow different sender email from IMAP user.
        msg['To'] = config.user

        if plain_text:
            msg.attach(MIMEText(plain_text, 'plain'))
        if html_text:
            msg.attach(MIMEText(html_text, 'html'))


        click.echo(f"\nWant to send out newsletter to {len(subscribers)} subscriber(s):\n\n" +
                   f"{(plain_text or html_text)[:300]} ...\n")
        if plain_text and html_text:
            click.echo(f"HTML body:\n\n{html_text[:300]} ...\n");

        if not dry_run and click.confirm('Do you want to proceed?'):
            server.sendmail(config.user, subscribers, msg.as_string())
            click.echo(f"Sent \"{title}\" to {len(subscribers)} subscriber(s)")
        elif dry_run:
            click.echo(f"Would have sent \"{title}\" to {len(subscribers)} subscriber(s)")
        else:
            click.echo(f"Did not send \"{title}\"")

        server.quit()


@cli.command()
@click.argument('filepath', type=click.File('r'))
@click.argument('alternative', type=click.File('r'), required=False)
@click.option('--subject', type=str)
@click.option('--dry-run', is_flag=True)
@click.pass_obj
def send_email(config, filepath, alternative, subject, dry_run):
    """Send email with content at given path(s) to all subscribers."""
    ensure_config(config)

    subscribers = sync_subscribers(config)
    click.echo(subscribers)
    
    def is_html(filepath: str):
        return filepath.endswith('.html')


    is_filepath_html = is_html(filepath.name)
    is_alternative_html = alternative and is_html(alternative.name)
    if alternative:
        if is_filepath_html and is_alternative_html:
            raise click.UsageError(
                "Both files are HTML; you should provide 1 HTML file and 1 plain text file"
            )
        if not is_filepath_html and not is_alternative_html:
            raise click.UsageError(
                "Neither file is HTML; you should provide 1 HTML file and 1 plain text file"
            )

    body = filepath.read()
    if not alternative:
        plain_text = None if is_filepath_html else body
        html_text = body if is_filepath_html else None
    else:
        alt_body = alternative.read()
        plain_text = alt_body if is_filepath_html else body
        html_text = body if is_filepath_html else alt_body

    send_email_func(config, html_text, plain_text, subject, subscribers, dry_run)
