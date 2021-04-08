import collections
import datetime
import random
import requests
import time
import parser_base
import datetime_util as dt


class Error(Exception):
    pass


class ReserveCaliforniaParser(parser_base.Parser):

    def _FuzzySleep(self):
        sleep_time_secs = random.uniform(1.0, 5.0)
        self.logger.Log('Sleeping for %s...' % sleep_time_secs)
        time.sleep(sleep_time_secs)

    def _FormatDateForPost(self, date):
        return date.strftime(r'%m/%d/%Y')

    def _GetHeaders(self):
        # Use these headers so that requests aren't rejected because its a script calling them.
        return {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/json',
            'origin': 'https://www.reservecalifornia.com',
            'referer': 'https://www.reservecalifornia.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
        }

    def _GetPostData(self, campsite, start_date):
        start_date_formatted = self._FormatDateForPost(start_date)
        max_date = start_date + datetime.timedelta(days=6*30)
        max_date_formatted = self._FormatDateForPost(max_date)
        data = {
            "FacilityId": campsite.facility_id,
            "UnitTypeId": 0,
            "StartDate": start_date_formatted,
            "InSeasonOnly": True,
            "WebOnly": True,
            "IsADA": False,
            "SleepingUnitId": 0,
            "MinVehicleLength": 0,
            "UnitCategoryId": 0,
            "UnitTypesGroupIds": [],
            "MinDate": start_date_formatted,
            "MaxDate": max_date_formatted}
        return data


    def _ValidateAndParseUnit(self, unit):
        site_name = unit.get('ShortName')
        if not site_name:
            return False, 'ShortName field missing from Unit info'

        slices = unit.get('Slices')
        if not slices:
            return False, 'Slices field missing/empty from Unit info'

        available_dates = []
        for s in slices.values():
            str_date = s.get('Date')
            if not str_date:
                return False, 'Date field missing from Unit Info'

            if 'IsFree' not in s:
                return False, 'IsFree field missing from Unit info'
            is_available = s.get('IsFree')
            if is_available:
                date = datetime.datetime.strptime(str_date, r'%Y-%m-%d')
                available_dates.append(date)

        return True, (site_name, available_dates)

    def _GetAvailability(self, campsite, start_date, site_to_available_dates):
        """Gets availability 20 days after start date from reservecalifornia.

        Doesn't return anything but updates the site_to_available_dates dict.
        """
        self.logger.Log('Getting availability data from start_date %s' % dt.FormatDate(start_date))
        data = self._GetPostData(campsite, start_date)
        response = requests.post(
            'https://calirdr.usedirect.com/rdr/rdr/search/grid',
            json=data,
            headers=self._GetHeaders())

        if response.status_code != 200:
            raise Error('Receive http code %s instead of 200' % first_response.status_code)

        self.logger.Log('Parsing response as json')
        json_response = response.json()
        facility = json_response.get('Facility')
        if not facility:
            raise Error('Facility entry not found in json response')
        units = facility.get('Units')
        if not units:
            raise Error('Units entry not found in json response')

        self.logger.Log('Processing %s units' % len(units))
        for unit in units.values():
            is_valid, invalid_reason_or_parsed_result = self._ValidateAndParseUnit(unit)
            if not is_valid:
                reason = invalid_reason_or_parsed_result
                self.logger.Log('Found invalid unit "%s" because %s ...' % (unit, reason))
                continue
            self.logger.Log('Found valid Unit')
            site, available_dates = invalid_reason_or_parsed_result
            self.logger.Log('Site: %s, available_dates: %s' % (site, available_dates))
            site_to_available_dates[site].extend(available_dates)
        self.logger.Log('Finished processing request response')


    def ParseAvailability(self, campsite, start_date, end_date):
        """Gets availability between start_date and end_date from reserveamerica for the specified campsite.

        Returns site_to_available_dates dict.
        """
        self.logger.Log('Retrieving availability from %s to %s' % (dt.FormatDate(start_date), dt.FormatDate(end_date)))
        site_to_available_dates = collections.defaultdict(list)
        while start_date < end_date:
            self._GetAvailability(campsite, start_date, site_to_available_dates)
             # Each self._GetAvailability call gets 20 days data so now we increment by 21
             # and loop again. TODO: Refactor this so we are not hard coding this number anymore
            start_date += datetime.timedelta(days=21)
            self._FuzzySleep()
        return site_to_available_dates

