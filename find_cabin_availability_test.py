import datetime
import find_cabin_availability
import logger

class TestQuitePeriod(object):

    def __init__(self):
        # Setup.
        self.sleep_calls = []
        self.MockOutSleep()

    def MockOutSleep(self):
        def MockSleep(secs):
            print('called mock sleep')
            self.sleep_calls.append(secs/60/60)
        find_cabin_availability.time.sleep = MockSleep

    def MockOutNow(self, hour):
        def MockNow(tz):
            print('called mock now')
            return datetime.datetime(hour=hour, day=1, month=1, year=2000, tzinfo=tz)
        find_cabin_availability.dt.Now = MockNow

    def testWaitIfQuitePeriod_QuitePeriodSpansSameDay(self):
        # First set of tests with quite period that doesn't span multiple days.
        lgr = logger.Logger(True)

        # Now is before quite period.
        self.MockOutNow(0)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        # Now is at start of quite period.
        self.MockOutNow(1)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        # Now is in quite period.
        self.MockOutNow(2)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        # Now is in quite period.
        self.MockOutNow(5)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        # Now is near end of quite period.
        self.MockOutNow(7)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        # Now is at end of quite period.
        self.MockOutNow(8)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        # Now is after quite period.
        self.MockOutNow(9)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        # Now is at end of day and after quite period.
        self.MockOutNow(23)
        find_cabin_availability.WaitIfQuitePeriod(1, 8, lgr)

        print(self.sleep_calls)
        assert len(self.sleep_calls) == 4
        assert self.sleep_calls == [7, 6, 3, 1]


    def testWaitIfQuitePeriod_QuitePeriodSpan2Days(self):
        # Second set of tests with quite period that spans multiple days.
        lgr = logger.Logger(True)

        # Now is before quite period.
        self.MockOutNow(21)
        find_cabin_availability.WaitIfQuitePeriod(22, 8, lgr)

        # Now is at start of quite period.
        self.MockOutNow(22)
        find_cabin_availability.WaitIfQuitePeriod(22, 8, lgr)

        # Now is in quite period.
        self.MockOutNow(23)
        find_cabin_availability.WaitIfQuitePeriod(22, 8, lgr)

        # Now is in quite period but crossed days.
        self.MockOutNow(0)
        find_cabin_availability.WaitIfQuitePeriod(22, 8, lgr)

        # Now is near end of quite period.
        self.MockOutNow(7)
        find_cabin_availability.WaitIfQuitePeriod(22, 8, lgr)

        # Now is at end of quite period.
        self.MockOutNow(8)
        find_cabin_availability.WaitIfQuitePeriod(22, 8, lgr)

        # Now is after quite period.
        self.MockOutNow(9)
        find_cabin_availability.WaitIfQuitePeriod(22, 8, lgr)

        print(self.sleep_calls)
        assert len(self.sleep_calls) == 4
        assert self.sleep_calls == [10, 9, 8, 1]




if __name__ == "__main__":
    TestQuitePeriod().testWaitIfQuitePeriod_QuitePeriodSpansSameDay()
    TestQuitePeriod().testWaitIfQuitePeriod_QuitePeriodSpan2Days()

