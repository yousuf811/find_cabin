import campsites
import email_sender
import logger
import re
import datetime

class MockCampsite(campsites.Campsite):
    name = 'Mock Campsite'
    site_regex = re.compile(r'.*')


if __name__ == '__main__':
    print('To run this test modify it locally with correct credentials.')
    lgr = logger.Logger(True)
    es = email_sender.EmailSender(
        MockCampsite, '<ADMIN_EMAIL>', '<FROM_EMAIL>', '<PASSWORD>',
        ['<TO_EMAIL>'], lgr)
    site_to_avail_dates = {'TestCamp': [datetime.datetime.now()]}
    es.SendEmail(datetime.datetime.now(), datetime.datetime.now(), site_to_avail_dates)
    es.SendFailureEmail(datetime.datetime.now(), datetime.datetime.now(), NotImplementedError('test failure'))
