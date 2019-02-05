import datetime

DATE_FORMAT = '%a %b %d %Y'  # Wed Jan 14 2015


def Now(tz):
    return datetime.datetime.now(tz)


def FormatDate(date):
    # Be careful when changing this method since it is also used in
    # constructing the POST body.
    return date.strftime(DATE_FORMAT)
