import bs4
import collections
import datetime
import pytz
import random
import requests
import smtplib
import sys
import time
import traceback

from email.mime.text import MIMEText

# Need to be set by command line arguments.
FROM_EMAIL = ''  # Needs to be a gmail address
FROM_EMAIL_PASSWORD = ''
TO_EMAILS = []

LOG_STRING = []
DATE_FORMAT = '%a %b %d %Y'  # Wed Jan 14 2015
REQUEST_URL = 'http://www.reserveamerica.com/camping/mount-tamalpais-sp/r/campgroundDetails.do?contractCode=CA&parkId=120063'
BASE_FORM_PARAMS = {
    'contractCode': 'CA',
    'parkId': '120063',
    'siteTypeFilter': 'ALL',
    'availStatus': '',
    'submitSiteForm': 'true',
    'search': 'site',
    'lengthOfStay': '1',
    'campingDateFlex': '',
    'currentMaximumWindow': '12',
    'contractDefaultMaxWindow': 'MS:24,LT:18,GA:24',
    'stateDefaultMaxWindow': 'MS:24,GA:24',
    'defaultMaximumWindow': '12',
    'loop': '',
    'siteCode': '',
    'lookingFor': '',
    'camping_2001_3013': '',
    'camping_2001_218': '',
    'camping_2002_3013': '',
    'camping_2002_218': '',
    'camping_2003_3012': '',
    'camping_3100_3012': '',
    'camping_10001_3012': '',
    'camping_10001_218': '',
    'camping_3101_3012': '',
    'camping_3101_218': '',
    'camping_9002_3012': '',
    'camping_9002_3013': '',
    'camping_9002_218': '',
    'camping_9001_3012': '',
    'camping_9001_218': '',
    'camping_3001_3013': '',
    'camping_2004_3013': '',
    'camping_2004_3012': '',
    'camping_3102_3012': '',}


class Error(Exception):
    pass


# General purpose methods.
def Log(message):
    global LOG_STRING
    print message
    LOG_STRING.append(message)


def FormatDate(date):
    # Be careful when changing this method since it is also used in
    # constructing the POST body.
    return date.strftime(DATE_FORMAT)


def FuzzySleep():
    sleep_time_secs = random.uniform(1.0, 5.0)
    Log('Sleeping for %s...' % sleep_time_secs)
    time.sleep(sleep_time_secs)


def GetPostData(date):
    form_params = dict(BASE_FORM_PARAMS)
    form_params['campingDate'] = FormatDate(date)
    return form_params


# Email related methods
def MakeSubjectAndMessage(start_date, end_date, site_to_available_dates):
    Log('Preparing subject for email...')
    subject = 'Steep Ravine Availability %s to %s' % (FormatDate(start_date), FormatDate(end_date))

    Log('Preparing message for email...')
    message = '%s\n\n' % subject
    date_to_cabins = collections.defaultdict(list)
    for site, dates in site_to_available_dates.iteritems():
        for date in dates:
            date_to_cabins[date].append(site)

    for date in sorted(date_to_cabins.iterkeys()):
        cabins = sorted(date_to_cabins[date])
        cabins_str = '  '.join(cabins)
        message += '%s:  %s\n' % (FormatDate(date), cabins_str)
    Log(message)
    return subject, message


def MakeFailureSubjectAndMessage(start_date, end_date, error):
    global LOG_STRING
    subject = 'Scraper failed when searching between %s to %s' % (FormatDate(start_date), FormatDate(end_date))
    message = 'Encountered error of type: %s\n' % type(error)
    message += '%s\n' % traceback.format_exc()
    message += 'Log:\n%s' % '\n'.join(LOG_STRING)
    return subject, message


def SendEmail(subject, message):
    message = MIMEText(message)
    message['Subject'] = subject
    message['From'] = FROM_EMAIL
    message['To'] = ','.join(TO_EMAILS)

    Log('Creating smtp server')
    server = smtplib.SMTP('smtp.gmail.com', 587)
    Log('\tstarttls')
    server.starttls()
    Log('\tehlo')
    server.ehlo()
    Log('\tlogin')
    server.login(FROM_EMAIL, FROM_EMAIL_PASSWORD)
    Log('\tsendmail')
    server.sendmail(FROM_EMAIL, TO_EMAILS, message.as_string())
    Log('\tquit')
    server.quit()


# HTML parsing related methods.
def GetTable(soup):
    table = soup.body.find("table", id='calendar')
    if not table:
        raise Error('Could not find table with id: calendar.')
    return table


def GetRows(table):
    rows = table.tbody.find_all('tr')
    if not rows:
        raise Error('Cound not find any rows in table')
    return rows


def IsAvailable(cell):
    return cell.string and cell.string == 'A'


def GetStatusCells(row):
    status_cells = row.find_all('td', class_='status')
    if not status_cells:
        raise Error('No status cells found in table.')
    return status_cells


def GetSiteName(row):
    site_name_tag = row.find(class_='siteListLabel')
    if not site_name_tag:
        raise Error('Could not find any html tag with class=siteListLabel')
    return site_name_tag.string


def IsValidRow(row):
    # The calendar table has rows for alignment etc. that don't have actual
    # availability data. This is a crappy way of ignoring them.
    cells = row.find_all('td')
    if not cells:
        return False
    if len(cells) < 3:
        return False
    return True


def GetAvailableDates(status_cells, start_date):
    available_dates = []
    index = 0
    for cell in status_cells:
        if IsAvailable(cell):
            time_delta = datetime.timedelta(days=index)
            date = start_date + time_delta
            available_dates.append(date)
        index += 1
    return available_dates


def GetAvailability(start_date, site_to_available_dates):
    """Gets availability on and 14 days after start date from reserveamerica.

    Doesn't return anything but updates the site_to_available_dates dict.
    """

    Log('Getting availability data from start_date %s' % FormatDate(start_date))
    session = requests.Session()

    Log('Starting GET request to setup session cookies etc.')
    session.get(REQUEST_URL)

    Log('Starting POST request to retrieve 2 week availability data')
    response = session.post(REQUEST_URL, data=GetPostData(start_date))

    # Debugging response.
    # print response.text
    # return

    if response.status_code != 200:
        raise Error('Receive http code %s instead of 200' % response.status_code)

    Log('Parsing response')
    soup = bs4.BeautifulSoup(response.text, 'html5lib')

    Log('Retreving calendar table')
    table = GetTable(soup)

    Log('Retrieving rows from calendar table')
    rows = GetRows(table)

    Log('Processing %s rows' % len(rows))
    for row in rows:
        Log('Checking if valid row')
        if IsValidRow(row):
            site_name = GetSiteName(row)

            Log('Getting status cells from row, site: %s' % site_name)
            status_cells = GetStatusCells(row)

            Log('Getting availability dates')
            available_dates = GetAvailableDates(status_cells, start_date)
            Log('Found %s available dates' % len(available_dates))
            if available_dates:
                site_to_available_dates[site_name].extend(available_dates)
        Log('Finished processing row')


def GetAvailabilityBetweenRange(start_date, end_date):
    """Gets availability between start_date and end_date from reserveamerica.

    Returns site_to_available_dates dict.
    """
    Log('Retrieving availability from %s to %s' % (FormatDate(start_date), FormatDate(end_date)))
    site_to_available_dates = collections.defaultdict(list)
    while start_date < end_date:
        GetAvailability(start_date, site_to_available_dates)
         # Each GetAvailability call gets 14 days data so now we increment by 14
         # and loop again.
        start_date += datetime.timedelta(days=14)
        FuzzySleep()
    return site_to_available_dates


def OnlyGetCabinAvailability(site_to_available_dates):
    Log('Selecting only cabins from availability...')
    cabin_to_availability_dates = {}
    for site, dates in site_to_available_dates.iteritems():
        if site.startswith('CB'):
            cabin_to_availability_dates[site] = dates
    return cabin_to_availability_dates


def Run():
    global LOG_STRING
    LOG_STRING = []
    today = datetime.date.today()
    start_date = today + datetime.timedelta(days=3)  # Searches fail unless they are 3 days from today.
    end_date = today + datetime.timedelta(days=6*30)  # Search up to 6 months.
    try:
        site_to_available_dates = GetAvailabilityBetweenRange(start_date, end_date)
        cabin_to_availability_dates = OnlyGetCabinAvailability(site_to_available_dates)
        Log('Found %s available cabins' % len(cabin_to_availability_dates))
        if cabin_to_availability_dates:
            subject, message = MakeSubjectAndMessage(start_date, end_date, cabin_to_availability_dates)
            SendEmail(subject, message)
    except BaseException as e:
        Log('Encountered exception:\n%s' % traceback.format_exc())
        subject, message = MakeFailureSubjectAndMessage(start_date, end_date, e)
        SendEmail(subject, message)
    Log('Finished')

def Now(tz):
    return datetime.datetime.now(tz)

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
        Log('In quite period, going to sleep for %s hours' % str(delta.seconds/(60.0*60.0)))
        time.sleep(delta.seconds)
        return


def PeriodicWait():
    # Run every hour with some fuzz.
    sleep_time_secs = (60*60) + random.uniform(10.0, 100.0)
    time.sleep(sleep_time_secs)


def main():
    if len(sys.argv) < 4:
        print 'Usage: find_cabin_availability.py <FROM_EMAIL> <FROM_EMAIL_PASSWORD> <TO_EMAIL> [<TO_EMAIL>] '
        sys.exit(-1)

    global FROM_EMAIL
    global FROM_EMAIL_PASSWORD
    global TO_EMAILS
    FROM_EMAIL = sys.argv[1]
    FROM_EMAIL_PASSWORD = sys.argv[2]
    TO_EMAILS = [to_email.strip() for to_email in sys.argv[3:]]
    while True:
        Run()
        #PeriodicWait()
        WaitIfQuitePeriod(23, 8)  # quite period is from 1am to 8am.


if __name__ == "__main__":
    main()