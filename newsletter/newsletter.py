#!/usr/bin/env python

import json
import os
from collections.abc import Callable
from typing import Optional

import click

from newsletter.config.config import Config
from newsletter.email_service.email_service import EmailService

CONFIG_FILEPATH = f"{os.path.dirname(os.path.realpath(__file__))}/config.json"

@click.group()
@click.pass_context
def cli(ctx):
    """The nwsl utility allows you to manage a lightweight newsletter. It tracks
    subscribers by scanning an inbox for emails with the words "subscribe" or
    "unsubscribe" in the subject line. It can then send out newsletter emails to
    these subscribers."""
    try:
        with open(CONFIG_FILEPATH, 'r') as config_file:
            config = json.load(config_file)
            assert config
            ctx.obj = Config.from_json(config)
    except (json.decoder.JSONDecodeError,
            KeyError,
            TypeError,
            AssertionError,
            FileNotFoundError) as error:
        ctx.obj = Config(error=error)


@cli.command()
def configure():
    """Edit the emailing config file. This starts the editor with the current
    contents of the config file. You can edit the following fields:

        sender - This is the sender name, probably the name of your newsletter.

        imap_host - The IMAP hostname of the subscriber-handling inbox.

        imap_user - The IMAP username of the subscriber-handling inbox.

        smtp_host - The SMTP hostname of the newsletter-sending email account.

        smtp_user - The SMTP username of the newsletter-sending email account.
    This is also used as the sender email address."""
    try:
        with open(CONFIG_FILEPATH, 'r') as config_file:
            config = json.dumps(json.load(config_file), ensure_ascii=False)
            assert config
    except (AssertionError, FileNotFoundError, json.decoder.JSONDecodeError):
        click.echo("Couldn't find/read config file; creating new one ...")
        config = """{
    "sender": "Sender Name",
    "imap_host": "mail.myhost.net",
    "imap_user": "mail@mydomain.net",
    "smtp_host": "mail.myhost.net",
    "smtp_user": "mail@mydomain.net"
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
    if (not config.sender or not config.imap_host or not config.imap_user or
        not config.smtp_host or not config.smtp_user):
        raise click.UsageError(
            "Config file contains empty value(s) (use \"nwsl configure\" to change it)",
        )

@cli.command()
@click.pass_obj
@click.option('--imap-password', prompt='IMAP password', hide_input=True,
              help='Your IMAP password. If empty, it prompts you for it.')
def subscribers(config, imap_password):
    """Print list of newsletter subscribers to stdout."""
    ensure_config(config)

    email_service = EmailService(config)
    click.echo('\n'.join(email_service.get_subscribers(imap_password)))

@cli.command()
@click.argument('file1', type=click.File('r'))
@click.argument('file2', type=click.File('r'), required=False)
@click.option('--dry-run', is_flag=True, help="Do not send any emails.")
@click.option('--imap-password', prompt='IMAP password', hide_input=True,
              help='Your IMAP password. If empty, it prompts you for it.')
@click.option('--smtp-password', prompt='SMTP password', hide_input=True,
              help='Your SMTP password. If empty, it prompts you for it.')
@click.pass_obj
def send_email(config, file1, file2, dry_run, imap_password, smtp_password):
    """Send email with content at given path(s) to all subscribers.

    The path(s) need to point to text files. If one is supplied, it can be
    either an HTML file (detected via the presence of an <html> tag) or a
    plain text file. If two are supplied, one of them needs to be an HTML file
    and the other a plain text file.

    Example:

        $ nwsl send-email ./newsletter.txt ./newsletter.html

    You will then be asked for your IMAP and SMTP passwords. There is a
    confirmation prompt before the emails are actually sent out to subscribers.

    If FILE1 is a single dash (``-''), nwsl reads from the standard input. Be
    careful, though, because when piping there'll be no confirmation prompt.
    Emails will be sent out.

    Example:

        $ cat ./newsletter.txt | sed -e 's/foo/bar/g' | nwsl send-email -

    """
    ensure_config(config)

    email_service = EmailService(config)

    click.echo(f"Fetching emails for {config.imap_user} at {config.imap_host}")
    active_subscribers = email_service.get_subscribers(imap_password)

    body = file1.read()
    alt_body = file2.read() if file2 else None

    def is_html(text: str):
        return '<html>' in text.lower()

    def get_text_matching(predicate: Callable[str, bool],
                          texts: list[Optional[str]]) -> Optional[str]:
        for text in texts:
            if text and predicate(text):
                return text
        return None
    html_text = get_text_matching(is_html, [body, alt_body])
    plain_text = get_text_matching(lambda text: not is_html(text), [body, alt_body])

    if file2 and not html_text:
        raise click.UsageError(
            "Neither file is HTML; you should provide 1 HTML file and 1 plain text file"
        )
    if file2 and not plain_text:
        raise click.UsageError(
            "Both files are HTML; you should provide 1 HTML file and 1 plain text file"
        )
    if not html_text and not plain_text:
        raise click.UsageError(
            "Found no input files; this should never happen"
        )

    email_service.send_email(html_text, plain_text, active_subscribers, dry_run,
                             smtp_password)
