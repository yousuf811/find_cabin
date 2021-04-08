import collections
import smtplib
import traceback
import datetime_util as dt


from email.mime.text import MIMEText


class EmailSender(object):

    def __init__(self, campsite, admin_email, from_email, from_email_password, to_emails, logger):
        self.campsite = campsite
        self.admin_email = admin_email
        self.from_email = from_email
        self.from_email_password = from_email_password
        self.to_emails = to_emails
        self.logger = logger

    def SendEmail(self, start_date, end_date, site_to_available_dates):
        subject, message = self._MakeSubjectAndMessage(start_date, end_date, site_to_available_dates)
        self._Send(subject, message, self.to_emails)

    def SendFailureEmail(self, start_date, end_date, error):
        subject, message = self._MakeFailureSubjectAndMessage(start_date, end_date, error)
        self._Send(subject, message, [self.admin_email])

    def _MakeSubjectAndMessage(self, start_date, end_date, site_to_available_dates):
        self.logger.Log('Preparing subject for email...')
        subject = '%s Availability %s to %s' % (self.campsite.name, dt.FormatDate(start_date), dt.FormatDate(end_date))

        self.logger.Log('Preparing message for email...')
        message = '%s\n\n' % subject
        date_to_sites = collections.defaultdict(list)
        for site, dates in site_to_available_dates.items():
            for date in dates:
                date_to_sites[date].append(site)

        for date in sorted(date_to_sites.keys()):
            sites = sorted(date_to_sites[date])
            sites_str = '  '.join(sites)
            message += '%s:  %s\n' % (dt.FormatDate(date), sites_str)
        self.logger.Log(message)
        return subject, message

    def _MakeFailureSubjectAndMessage(self, start_date, end_date, error):
        subject = 'Scraper failed when searching between %s to %s for %s' % (dt.FormatDate(start_date), dt.FormatDate(end_date), self.campsite.name)
        message = 'Encountered error of type: %s\n' % type(error)
        message += '%s\n' % traceback.format_exc()
        message += 'Log:\n%s' % '\n'.join(self.logger.GetBuffer())
        return subject, message


    def _Send(self, subject, message, to_emails):
        message = MIMEText(message)
        message['Subject'] = subject
        message['From'] = self.from_email
        message['To'] = ','.join(to_emails)

        self.logger.Log('Creating smtp server')
        server = smtplib.SMTP('smtp.mailgun.org', 587)
        self.logger.Log('\tstarttls')
        server.starttls()
        self.logger.Log('\tehlo')
        server.ehlo()
        self.logger.Log('\tlogin')
        server.login(self.from_email, self.from_email_password)
        self.logger.Log('\tsendmail')
        server.sendmail(self.from_email, to_emails, message.as_string())
        self.logger.Log('\tquit')
        server.quit()

