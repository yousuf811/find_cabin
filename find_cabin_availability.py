import bs4
import collections
import datetime
import pytz
import random
import re
import requests
import smtplib
import sys
import time
import traceback

from campsites import *
from email.mime.text import MIMEText

USAGE = """
    Usage:
        find_cabin_availability.py <FROM_EMAIL> <FROM_EMAIL_PASSWORD> <CAMPSITE_INFO> <CAMPSITE_INFO> ...

    where:
        FROM_EMAIL = the gmail address of the account from which notification emails will be sent.

        FROM_EMAIL_PASSWORD = the password for the FROM_EMAIL account.

        CAMPSITE_INFO = <CAMPSITE_CLASS_NAME>:<TO_EMAILS>

        CAMPSITE_CLASS_NAME = the name of one of the classes defined in campsites.py for which the script will
            attempt to find availability.

        TO_EMAILS = comma separated list of email addresses to which the notification emails will be sent for
            the corresponding campsite.
    """

DATE_FORMAT = '%a %b %d %Y'  # Wed Jan 14 2015

# TODO: Do something about improving the way we do logging.


class Error(Exception):
    pass


class Logger(object):
    """Special logging class that maintains a buffer of everything that has been logged."""

    def __init__(self):
        self.log_buffer = []

    def Log(self, message):
        print message
        self.log_buffer.append(message)

    def GetBuffer(self):
        return list(self.log_buffer)

    def ClearBuffer(self):
        self.log_buffer = []


class EmailSender(object):

    def __init__(self, campsite, from_email, from_email_password, to_emails, logger):
        self.campsite = campsite
        self.from_email = from_email
        self.from_email_password = from_email_password
        self.to_emails = to_emails
        self.logger = logger

    def SendEmail(self, start_date, end_date, site_to_available_dates):
        subject, message = self._MakeSubjectAndMessage(start_date, end_date, site_to_available_dates)
        self._Send(subject, message)

    def SendFailureEmail(self, start_date, end_date, error):
        subject, message = self._MakeFailureSubjectAndMessage(start_date, end_date, error)
        self._Send(subject, message)

    def _MakeSubjectAndMessage(self, start_date, end_date, site_to_available_dates):
        self.logger.Log('Preparing subject for email...')
        subject = '%s Availability %s to %s' % (self.campsite.name, FormatDate(start_date), FormatDate(end_date))

        self.logger.Log('Preparing message for email...')
        message = '%s\n\n' % subject
        date_to_sites = collections.defaultdict(list)
        for site, dates in site_to_available_dates.iteritems():
            for date in dates:
                date_to_sites[date].append(site)

        for date in sorted(date_to_sites.iterkeys()):
            sites = sorted(date_to_sites[date])
            sites_str = '  '.join(sites)
            message += '%s:  %s\n' % (FormatDate(date), sites_str)
        self.logger.Log(message)
        return subject, message

    def _MakeFailureSubjectAndMessage(self, start_date, end_date, error):
        subject = 'Scraper failed when searching between %s to %s for %s' % (FormatDate(start_date), FormatDate(end_date), self.campsite.name)
        message = 'Encountered error of type: %s\n' % type(error)
        message += '%s\n' % traceback.format_exc()
        message += 'Log:\n%s' % '\n'.join(self.logger.GetBuffer())
        return subject, message


    def _Send(self, subject, message):
        message = MIMEText(message)
        message['Subject'] = subject
        message['From'] = self.from_email
        message['To'] = ','.join(self.to_emails)

        self.logger.Log('Creating smtp server')
        server = smtplib.SMTP('smtp.gmail.com', 587)
        self.logger.Log('\tstarttls')
        server.starttls()
        self.logger.Log('\tehlo')
        server.ehlo()
        self.logger.Log('\tlogin')
        server.login(self.from_email, self.from_email_password)
        self.logger.Log('\tsendmail')
        server.sendmail(self.from_email, self.to_emails, message.as_string())
        self.logger.Log('\tquit')
        server.quit()


class AvailabilityFinder(object):

    def __init__(self, campsite, email_sender, logger):
        self.campsite = campsite
        self.email_sender = email_sender
        self.logger = logger

    def _FuzzySleep(self):
        sleep_time_secs = random.uniform(1.0, 5.0)
        self.logger.Log('Sleeping for %s...' % sleep_time_secs)
        time.sleep(sleep_time_secs)

    def _GetPostData(self, date):
        form_params = dict(self.campsite.form_params)
        form_params['campingDate'] = FormatDate(date)
        return form_params

    # HTML parsing related methods.
    def _GetTable(self, soup):
        table = soup.body.find("table", id='calendar')
        if not table:
            raise Error('Could not find table with id: calendar.')
        return table

    def _GetRows(self, table):
        rows = table.tbody.find_all('tr')
        if not rows:
            raise Error('Cound not find any rows in table')
        return rows

    def _IsAvailable(self, cell):
        return cell.string and cell.string == 'A'

    def _GetStatusCells(self, row):
        status_cells = row.find_all('td', class_='status')
        if not status_cells:
            raise Error('No status cells found in table.')
        return status_cells

    def _GetSiteName(self, row):
        site_name_tag = row.find(class_='siteListLabel')
        if not site_name_tag:
            raise Error('Could not find any html tag with class=siteListLabel')
        return site_name_tag.string

    def _IsValidRow(self, row):
        # The calendar table has rows for alignment etc. that don't have actual
        # availability data. This is a crappy way of ignoring them.
        cells = row.find_all('td')
        if not cells:
            return False
        if len(cells) < 3:
            return False
        return True

    def _GetAvailableDates(self, status_cells, start_date):
        available_dates = []
        index = 0
        for cell in status_cells:
            if self._IsAvailable(cell):
                time_delta = datetime.timedelta(days=index)
                date = start_date + time_delta
                available_dates.append(date)
            index += 1
        return available_dates

    def _GetAvailability(self, start_date, site_to_available_dates):
        """Gets availability on and 14 days after start date from reserveamerica for specified campsite.

        Doesn't return anything but updates the site_to_available_dates dict.
        """

        self.logger.Log('Getting availability data from start_date %s' % FormatDate(start_date))
        session = requests.Session()

        self.logger.Log('Starting GET request to setup session cookies etc.')
        session.get(self.campsite.request_url)

        self.logger.Log('Starting POST request to retrieve 2 week availability data')
        response = session.post(self.campsite.request_url, data=self._GetPostData(start_date))

        # Debugging response.
        # print response.text
        # return

        if response.status_code != 200:
            raise Error('Receive http code %s instead of 200' % response.status_code)

        self.logger.Log('Parsing response')
        soup = bs4.BeautifulSoup(response.text, 'html5lib')

        self.logger.Log('Retreving calendar table')
        table = self._GetTable(soup)

        self.logger.Log('Retrieving rows from calendar table')
        rows = self._GetRows(table)

        self.logger.Log('Processing %s rows' % len(rows))
        for row in rows:
            self.logger.Log('Checking if valid row')
            if self._IsValidRow(row):
                site_name = self._GetSiteName(row)

                self.logger.Log('Getting status cells from row, site: %s' % site_name)
                status_cells = self._GetStatusCells(row)

                self.logger.Log('Getting availability dates')
                available_dates = self._GetAvailableDates(status_cells, start_date)
                self.logger.Log('Found %s available dates' % len(available_dates))
                if available_dates:
                    site_to_available_dates[site_name].extend(available_dates)
            self.logger.Log('Finished processing row')


    def _GetAvailabilityBetweenRange(self, start_date, end_date):
        """Gets availability between start_date and end_date from reserveamerica for the specified campsite.

        Returns site_to_available_dates dict.
        """
        self.logger.Log('Retrieving availability from %s to %s' % (FormatDate(start_date), FormatDate(end_date)))
        site_to_available_dates = collections.defaultdict(list)
        while start_date < end_date:
            self._GetAvailability(start_date, site_to_available_dates)
             # Each self._GetAvailability call gets 14 days data so now we increment by 14
             # and loop again.
            start_date += datetime.timedelta(days=14)
            self._FuzzySleep()
        return site_to_available_dates


    def _FilterSiteAvailability(self, site_to_available_dates):
        self.logger.Log('Selecting only requested sites from availability...')
        requested_site_to_availability_dates = {}
        for site, dates in site_to_available_dates.iteritems():
            if self.campsite.site_regex.match(site):
                requested_site_to_availability_dates[site] = dates
        return requested_site_to_availability_dates


    def Run(self):
        self.logger.ClearBuffer()
        self.logger.Log('Starting search for %s' % self.campsite.name)
        today = datetime.date.today()
        start_date = today + datetime.timedelta(days=3)  # Searches fail unless they are 3 days from today.
        end_date = today + datetime.timedelta(days=6*30)  # Search up to 6 months.
        try:
            # First find availability of all reservable sites in this campsite.
            site_to_available_dates = self._GetAvailabilityBetweenRange(start_date, end_date)
            # Now filter out ones we don't care about.
            site_to_available_dates = self._FilterSiteAvailability(site_to_available_dates)
            self.logger.Log('Found %s available sites' % len(site_to_available_dates))
            if site_to_available_dates:
                self.email_sender.SendEmail(start_date, end_date, site_to_available_dates)
        except BaseException as e:
            self.logger.Log('Encountered exception:\n%s' % traceback.format_exc())
            self.email_sender.SendFailureEmail(start_date, end_date, e)
        self.logger.Log('Finished search for %s' % self.campsite.name)


def Now(tz):
    return datetime.datetime.now(tz)


def FormatDate(date):
    # Be careful when changing this method since it is also used in
    # constructing the POST body.
    return date.strftime(DATE_FORMAT)


def WaitIfQuitePeriod(start_hour, end_hour):
    """Waits if current time lies in a quite period until quite period ends.

    Args:
        start_hour: int, starting hour for quite period. Valid values are between 0-23.
        end_hour: int, ending hour for quite period. Valid values are between 0-23.
    """
    tz = pytz.timezone('US/Pacific')
    now = Now(tz)
    end_time = None
    if start_hour < end_hour:  # quite period does not span days.
        if  start_hour <= now.hour < end_hour:
            end_time = datetime.datetime(hour=end_hour, day=now.day, month=now.month, year=now.year, tzinfo=tz)
    else:  # quite period spans days.
        if now.hour >= start_hour:  # Now is in the first day of the quite period range, so increment day.
            end_time = datetime.datetime(hour=end_hour, day=now.day+1, month=now.month, year=now.year, tzinfo=tz)
        elif now.hour < end_hour:  # Now is in the second day of the quite period range, so keep same day.
            end_time = datetime.datetime(hour=end_hour, day=now.day, month=now.month, year=now.year, tzinfo=tz)

    if end_time:
        delta = end_time - now
        Logger().Log('In quite period, going to sleep for %s hours' % str(delta.seconds/(60.0*60.0)))
        time.sleep(delta.seconds)
        return


def PeriodicWait():
    # Run every hour with some fuzz.
    sleep_time_secs = (60*60) + random.uniform(10.0, 100.0)
    time.sleep(sleep_time_secs)


def ConstructAndValidateCampsiteInfo(campsite_info):
    parts = campsite_info.split(':')
    if len(parts) != 2:
        ErrorExit('Campsite Info "%s" is malformed.', campsite_info)

    campsite_class_str, to_emails_str = parts

    campsite_class = globals().get(campsite_class_str)
    if not campsite_class:
        ErrorExit('%s is not a valid campsite class name', campsite_class_str)
    if not hasattr(campsite_class, 'name'):
        ErrorExit('name static attribute not found on campsite class: %s', campsite_class_str)
    if not hasattr(campsite_class, 'request_url'):
        ErrorExit('request_url static attribute not found on campsite class: %s', campsite_class_str)
    if not hasattr(campsite_class, 'form_params'):
        ErrorExit('form_params static attribute not found on campsite class: %s', campsite_class_str)
    if not hasattr(campsite_class, 'site_regex'):
        ErrorExit('site_regex static attribute not found on campsite class: %s', campsite_class_str)

    to_emails = [e for e in to_emails_str.split(',') if e]
    return campsite_class, to_emails

def ErrorExit(msg, args=None):
    if args:
        msg = msg % args
    print msg
    sys.exit(-1)


def main():
    if len(sys.argv) < 4:
        ErrorExit(USAGE)

    from_email = sys.argv[1]  # Needs to be a gmail address
    from_email_password = sys.argv[2]
    finders = []
    for campsite_info in sys.argv[3:]:
        campsite, to_emails = ConstructAndValidateCampsiteInfo(campsite_info)
        logger = Logger()
        email_sender = EmailSender(campsite, from_email, from_email_password, to_emails, logger)
        availability_finder = AvailabilityFinder(campsite, email_sender, logger)
        finders.append(availability_finder)

    while True:
        for finder in finders:
            finder.Run()
        PeriodicWait()
        WaitIfQuitePeriod(23, 8)  # quite period is from 1am to 8am.


if __name__ == "__main__":
    main()