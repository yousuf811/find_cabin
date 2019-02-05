import pytz
import datetime_util

if __name__ == '__main__':
    now = datetime_util.Now(pytz.timezone('US/Pacific'))
    print(now)
    print(datetime_util.FormatDate(now))
