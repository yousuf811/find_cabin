import datetime
import pytz
import random
import time
import traceback
import sys

# Local modules
from campsites import *
import datetime_util as dt
import email_sender as es
import logger as lgr
import parser_ra
import parser_rc


USAGE = """
    Usage:
        find_cabin_availability.py <FROM_EMAIL> <FROM_EMAIL_PASSWORD> <ADMIN_EMAIL> <CAMPSITE_INFO> <CAMPSITE_INFO> ...

    where:
        FROM_EMAIL = the mailgun address of the account from which notification emails will be sent.

        FROM_EMAIL_PASSWORD = the password for the FROM_EMAIL account.

        ADMIN_EMAIL = the email address to which failure emails will be sent.

        CAMPSITE_INFO = <CAMPSITE_CLASS_NAME>:<TO_EMAILS>

        CAMPSITE_CLASS_NAME = the name of one of the classes defined in campsites.py for which the script will
            attempt to find availability.

        TO_EMAILS = comma separated list of email addresses to which the notification emails will be sent for
            the corresponding campsite.

        FLUSH_LOGS = optional, default is true. If set then on each run log will be flushed to a local file.
    """

RUN_FREQUENCY_SECS = 60*10  # How often the availability finder should run.
EMAIL_FREQUENCY_SECS = 60*60*24  # How often we should send availability emails regardless of whether it changes, currently every 24 hours.

# TODO: Do something about improving the way we do logging.

class AvailabilityFinder(object):

    def __init__(self, campsite, email_sender, parser, logger):
        self.campsite = campsite
        self.email_sender = email_sender
        self.parser = parser
        self.logger = logger
        self.last_result = None  # The last availability result.
        self.last_email_time = None  # The last time in secs we sent an availability email.

    def _FilterSiteAvailability(self, site_to_available_dates):
        self.logger.Log('Selecting only requested sites from availability...')
        requested_site_to_availability_dates = {}
        for site, dates in site_to_available_dates.items():
            if self.campsite.site_regex.match(site):
                requested_site_to_availability_dates[site] = dates
        return requested_site_to_availability_dates

    def _ShouldSendEmail(self, site_to_available_dates):
        """Only send email if the last_result is different from the new result or if it has been
        greater than EMAIL_FREQUENCY_SECS since we last sent an email.."""
        now = time.time()
        if self.last_result != site_to_available_dates:
            self.last_result = dict(site_to_available_dates)
            self.last_email_time = now
            return True
        # If the availability hasn't changed but it has been more than EMAIL_FREQUENCY_SECS
        # since we sent an email, send it again anyway.
        if (now - self.last_email_time > EMAIL_FREQUENCY_SECS):
            self.last_email_time = now
            return True
        return False

    def Run(self):
        self.logger.Log('Starting search for %s' % self.campsite.name)
        today = datetime.date.today()
        start_date = today + datetime.timedelta(days=1)
        end_date = today + datetime.timedelta(days=6*30)  # Search up to 6 months.
        try:
            # First find availability of all reservable sites in this campsite.
            site_to_available_dates = self.parser.ParseAvailability(self.campsite, start_date, end_date)
            # Now filter out ones we don't care about.
            site_to_available_dates = self._FilterSiteAvailability(site_to_available_dates)
            self.logger.Log('Found %s available sites' % len(site_to_available_dates))
            if self._ShouldSendEmail(site_to_available_dates):
                self.logger.Log('Sending email')
                self.email_sender.SendEmail(start_date, end_date, site_to_available_dates)
            else:
                self.logger.Log('Not sending email.')
        except BaseException as e:
            self.logger.Log('Encountered exception:\n%s' % traceback.format_exc())
            self.logger.Log('Sending failure email')
            self.email_sender.SendFailureEmail(start_date, end_date, e)
        self.logger.Log('Finished search for %s' % self.campsite.name)


def WaitIfQuitePeriod(start_hour, end_hour, logger):
    """Waits if current time lies in a quite period until quite period ends.

    Args:
        start_hour: int, starting hour for quite period. Valid values are between 0-23.
        end_hour: int, ending hour for quite period. Valid values are between 0-23.
    """
    tz = pytz.timezone('US/Pacific')
    now = dt.Now(tz)
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
        logger.Log('In quite period, going to sleep for %s hours' % str(delta.seconds/(60.0*60.0)))
        time.sleep(delta.seconds)
        return


def PeriodicWait():
    # Run every RUN_FREQUENCY_SECS with some fuzz.
    sleep_time_secs = (RUN_FREQUENCY_SECS) + random.uniform(10.0, 100.0)
    time.sleep(sleep_time_secs)


def ConstructAndValidateCampsiteInfo(campsite_info):
    parts = campsite_info.split(':')
    if len(parts) != 2:
        ErrorExit('Campsite Info "%s" is malformed.', campsite_info)

    campsite_class_str, to_emails_str = parts

    campsite_class = globals().get(campsite_class_str)
    if not campsite_class:
        ErrorExit('%s is not a valid campsite class name', campsite_class_str)

    if not issubclass(campsite_class, Campsite):
        ErrorExit('%s class should be a subclass of campsites.Campsite', campsite_class_str)
    is_valid, err_msg = campsite_class.Validate()
    if not is_valid:
        ErrorExit(err_msg)

    to_emails = [e for e in to_emails_str.split(',') if e]
    return campsite_class, to_emails


def GetParser(campsite, logger):
    if issubclass(campsite, ReserveAmericaCampsite):
        parser_class = parser_ra.ReserveAmericaParser
    elif issubclass(campsite, ReserveCaliforniaCampsite):
        parser_class = parser_rc.ReserveCaliforniaParser
    return parser_class(logger)


def ErrorExit(msg, args=None):
    if args:
        msg = msg % args
    print(msg)
    sys.exit(-1)


def main():
    if len(sys.argv) < 5:
        ErrorExit(USAGE)

    from_email = sys.argv[1]  # Needs to be a mailgun address
    from_email_password = sys.argv[2]
    admin_email = sys.argv[3]
    finders = []
    logger = lgr.Logger(False)  # Set this to True for debugging.
    for campsite_info in sys.argv[4:]:
        campsite, to_emails = ConstructAndValidateCampsiteInfo(campsite_info)
        email_sender = es.EmailSender(campsite, admin_email, from_email, from_email_password, to_emails, logger)
        parser = GetParser(campsite, logger)
        availability_finder = AvailabilityFinder(campsite, email_sender, parser, logger)
        finders.append(availability_finder)

    while True:
        for finder in finders:
            finder.Run()
            logger.ClearBuffer()
        PeriodicWait()
        WaitIfQuitePeriod(23, 8, logger)  # quite period is from 1am to 8am.


if __name__ == "__main__":
    main()