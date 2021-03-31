#!/usr/bin/env python3

import email
import imaplib
import re
import smtplib
import ssl
import sys
import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import click
from newsletter.config.config import Config


class EmailService:
    """This class reads & sends newsletter emails."""

    def __init__(self, config: Config):
        self.config = config

    def get_subscribers(self, imap_password: str) -> list[str]:
        """Fetch emails and return list of subscribers."""

        imap_server = imaplib.IMAP4_SSL(host=self.config.imap_host)
        imap_server.login(self.config.imap_user, imap_password)
        imap_server.select()

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
                subscribers.remove(sender_email)
            elif 'subscribe' in subject.lower() and not sender_email in subscribers:
                subscribers.append(sender_email)

        return subscribers

    def send_email(self,
                   html_text: Optional[str],
                   plain_text: Optional[str],
                   subscribers: list[str],
                   dry_run: bool,
                   smtp_password: str):
        def find_title_in_html(html: str) -> Optional[str]:
            result = re.search(r"<h1>(.+)<\/h1>", html)
            return result.group(1) if result else None

        def find_title_in_markdown(md: str) -> Optional[str]:
            result = re.search(r"# (.+)", md)
            return result.group(1) if result else None

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
                self.config.smtp_host, 465, context=context
        ) as server:
            server.login(self.config.smtp_user, smtp_password)

            title = (html.unescape(find_title_in_html(html_text))
                     if html_text
                     else find_title_in_markdown(plain_text)) or 'Untitled'

            msg = MIMEMultipart('alternative')
            msg['Subject'] = title
            msg['From'] = f"{self.config.sender} <{self.config.smtp_user}>"
            msg['To'] = self.config.smtp_user

            if plain_text:
                msg.attach(MIMEText(plain_text, 'plain'))
            if html_text:
                msg.attach(MIMEText(html_text, 'html'))

            click.echo(f"\nWant to send out newsletter to {len(subscribers)} subscriber(s):\n\n" +
                       f"{(plain_text or html_text)[:300]} ...\n")
            if plain_text and html_text:
                click.echo(f"HTML body:\n\n{html_text[:300]} ...\n")

            # Here we need to check whether we're reading from stdin. If we are,
            # then we can ask the user for confirmation before sending the
            # email. If not, the command is being used in a pipe, meaning we
            # can't present a confirmation dialog (this is a limitation in
            # Click), so we just go ahead & send the email without confirmation.
            if (not dry_run and (not sys.stdin.isatty() or
                               click.confirm('Do you want to proceed?'))):
                server.sendmail(self.config.smtp_user, subscribers, msg.as_string())
                click.echo(f"Sent \"{title}\" to {len(subscribers)} subscriber(s)")
            elif dry_run:
                click.echo(f"Would have sent \"{title}\" to {len(subscribers)} subscriber(s)")
            else:
                click.echo(f"Did not send \"{title}\"")

            server.quit()
