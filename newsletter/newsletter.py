#!/usr/bin/env python

import json
import os

import click

from newsletter.email_service.email_service import EmailService
from newsletter.config.config import Config


CONFIG_FILEPATH = f"{os.path.dirname(os.path.realpath(__file__))}/config.json"

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

@cli.command()
@click.argument('filepath', type=click.File('r'))
@click.argument('alternative', type=click.File('r'), required=False)
@click.option('--dry-run', is_flag=True)
@click.pass_obj
def send_email(config, filepath, alternative, dry_run):
    """Send email with content at given path(s) to all subscribers."""
    ensure_config(config)

    email_service = EmailService(config)

    subscribers = email_service.get_subscribers()
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

    email_service.send_email(html_text, plain_text, subscribers, dry_run)
