from unittest import TestCase, main, mock

from click.testing import CliRunner
from newsletter.newsletter import cli


class TestNewsletter(TestCase):

    # nwsl subscribers

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    def test_subscribers(self, mock_get_subscribers):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        runner = CliRunner()
        result = runner.invoke(cli, ['subscribers'], input='xyz\n')
        self.assertIn(subscribers[0], result.output)
        self.assertIn(subscribers[1], result.output)
        self.assertEqual(0, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    def test_subscribers_with_pw_option(self, mock_get_subscribers):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        runner = CliRunner()
        result = runner.invoke(cli, ['subscribers', '--imap-password=xyz'])
        self.assertEqual('\n'.join(subscribers) + '\n', result.output)
        self.assertEqual(0, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    def test_subscribers_empty_with_pw_option(self, mock_get_subscribers):
        mock_get_subscribers.return_value = []
        runner = CliRunner()
        result = runner.invoke(cli, ['subscribers', '--imap-password=xyz'])
        self.assertEqual('\n', result.output)
        self.assertEqual(0, result.exit_code)

    # nwsl send-email

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    @mock.patch('newsletter.newsletter.EmailService.send_email')
    def test_send_email_without_input(
            self, mock_send_email, mock_get_subscribers
    ):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        mock_send_email.return_value = None

        runner = CliRunner()
        result = runner.invoke(cli, ['send-email'], input='foo\nbar\n')

        self.assertIn('Missing argument', result.output)
        self.assertEqual(2, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    @mock.patch('newsletter.newsletter.EmailService.send_email')
    def test_send_email_plain(self, mock_send_email, mock_get_subscribers):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        mock_send_email.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            text = 'Tell me, Muse, of the man of many ways ...'
            with open('hello.txt', 'w') as f:
                f.write(text)

            result = runner.invoke(cli, ['send-email', './hello.txt'],
                                   input='foo\nbar\n')

            mock_send_email.assert_called_once_with(
                None, text, subscribers, False, 'bar'
            )
            self.assertEqual(0, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    @mock.patch('newsletter.newsletter.EmailService.send_email')
    def test_send_email_html(self, mock_send_email, mock_get_subscribers):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        mock_send_email.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            text = '<html><body>Tell me, Muse ...</body></html>'
            with open('hello.html', 'w') as f:
                f.write(text)

            result = runner.invoke(cli, ['send-email', './hello.html'],
                                   input='foo\nbar\n')

            mock_send_email.assert_called_once_with(
                text, None, subscribers, False, 'bar'
            )
            self.assertEqual(0, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    @mock.patch('newsletter.newsletter.EmailService.send_email')
    def test_send_email_plain_and_html(
            self, mock_send_email, mock_get_subscribers
    ):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        mock_send_email.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            plain = 'Tell me, Muse, of the man of many ways ...'
            html = '<html><body>Tell me, Muse ...</body></html>'
            with open('hello.txt', 'w') as f:
                f.write(plain)
            with open('hello.html', 'w') as f:
                f.write(html)

            result = runner.invoke(
                cli,
                ['send-email', './hello.html', './hello.txt'],
                input='foo\nbar\n'
            )

            mock_send_email.assert_called_once_with(
                html, plain, subscribers, False, 'bar'
            )
            self.assertEqual(0, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    @mock.patch('newsletter.newsletter.EmailService.send_email')
    def test_send_email_html_and_plain(
            self, mock_send_email, mock_get_subscribers
    ):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        mock_send_email.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            html = '<html><body>Tell me, Muse ...</body></html>'
            plain = 'Tell me, Muse, of the man of many ways ...'
            with open('hello.html', 'w') as f:
                f.write(html)
            with open('hello.txt', 'w') as f:
                f.write(plain)

            result = runner.invoke(
                cli,
                ['send-email', './hello.txt', './hello.html'],
                input='foo\nbar\n'
            )

            mock_send_email.assert_called_once_with(
                html, plain, subscribers, False, 'bar'
            )
            self.assertEqual(0, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    @mock.patch('newsletter.newsletter.EmailService.send_email')
    def test_send_email_two_plain(self, mock_send_email, mock_get_subscribers):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        mock_send_email.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            text1 = 'Tell me, Muse, '
            text2 = 'of the man of many ways ...'
            with open('hello1.txt', 'w') as f:
                f.write(text1)
            with open('hello2.text', 'w') as f:
                f.write(text2)

            result = runner.invoke(
                cli,
                ['send-email', './hello1.text', './hello2.txt'],
                input='foo\nbar\n'
            )

            mock_send_email.assert_not_called()
            self.assertEqual(2, result.exit_code)

    @mock.patch('newsletter.newsletter.EmailService.get_subscribers')
    @mock.patch('newsletter.newsletter.EmailService.send_email')
    def test_send_email_two_html(self, mock_send_email, mock_get_subscribers):
        subscribers = ['one@example.net', 'two@example.net']
        mock_get_subscribers.return_value = subscribers
        mock_send_email.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            html1 = '<html><body>Tell me, Muse,</body></html>'
            html2 = '<html><body>of the man of many ways ...</body></html>'
            with open('hello1.html', 'w') as f:
                f.write(html1)
            with open('hello2.html', 'w') as f:
                f.write(html2)

            result = runner.invoke(
                cli,
                ['send-email', './hello1.html', './hello2.html'],
                input='foo\nbar\n'
            )

            mock_send_email.assert_not_called()
            self.assertEqual(2, result.exit_code)
            
if __name__ == '__main__':
    main()
