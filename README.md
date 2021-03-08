# nwsl

`nwsl` is a command-line utility for running a lightweight, serverless
newsletter. Well, it's not serverless exactly: it tracks subscribers by scanning
a mailbox for emails with the words "subscribe" or "unsubscribe" in the subject
line. It then allows you to send out newsletter emails to these subscribers,

```sh
$ nwsl send-email /path/to/newsletter.txt /path/to/newsletter.html
IMAP password:
SMTP password:
Fetching emails for newsletter@example.net at mail.host.net

Want to send out newsletter to 3 subscriber(s):

# My Newsletter Title

This here is the plain text version ...

HTML body:

<html>
    <head></head>
    <body>
        <p>This here is the HTMl version</p> ...

Do you want to proceed? [Y/n]: y
Sent "My Newsletter Title" to 3 subscriber(s)
```

but more about this below.

`nwsl` is currently in alpha. I'm looking to add more features & would be happy to get feature requests or contributions.

## Installation

## Set-up

In order to use `nwsl`, you first need to set up a suitable email inbox. You'll then want to instruct prospective subscribers to send an email to this address with "subscribe" in the subject line. You'll probably also want to add instructions for unsubscribing in your newsletter emails; to unsubscribe, subscribers need to send an email to the same address with "unsubscribe" in the subject line.

For example, on your blog:

> You can subscribe by sending an email with "subscribe" in the subject line to newsletter@example.net.

And in your newsletter emails:

> To unsubscribe, simply send an email to newsletter@example.net with the word "unsubscribe" in the subject line.

Finally, you'll need to run `nwsl configure` (see below).

## Commands

### `nwsl configure`

```sh
Usage: nwsl configure [OPTIONS]

  Edit the emailing config file. This starts the editor with the current
  contents of the config file. You can edit the following fields:

      sender - This is the sender name, probably the name of your
      newsletter.

      imap_host - The IMAP hostname of the subscriber-handling inbox.

      imap_user - The IMAP username of the subscriber-handling inbox.

      smtp_host - The SMTP hostname of the newsletter-sending email account.

      smtp_user - The SMTP username of the newsletter-sending email account.
      This is also used as the sender email address.

Options:
  --help  Show this message and exit.
```

### `nwsl subscribers`

```sh
Usage: nwsl subscribers [OPTIONS]

  Print list of newsletter subscribers to stdout.

Options:
  --imap-password TEXT  Your IMAP password. If empty, it prompts you for it.
  --help                Show this message and exit.
```

### `nwsl send-email`

```sh
Usage: nwsl send-email [OPTIONS] FILE1 [FILE2]

  Send email with content at given path(s) to all subscribers.

  The path(s) need to point to text files. If one is supplied, it can be
  either an HTML file (detected via the presence of an <html> tag) or a
  plain text file. If two are supplied, one of them needs to be an HTML file
  and the other a plain text file.

  Example:

      $ nwsl send-email ./newsletter.txt ./newsletter.html

  You will then be asked for your IMAP and SMTP passwords. There is a
  confirmation prompt before the emails are actually sent out to
  subscribers.

  If FILE1 is a single dash (``-''), nwsl reads from the standard input. Be
  careful, though, because when piping there'll be no confirmation prompt.
  Emails will be sent out.

  Example:

      $ cat ./newsletter.txt | sed -e 's/foo/bar/g' | nwsl send-email -

Options:
  --dry-run             Do not send any emails.
  --imap-password TEXT  Your IMAP password. If empty, it prompts you for it.
  --smtp-password TEXT  Your SMTP password. If empty, it prompts you for it.
  --help                Show this message and exit.
```
