import parser_base
import bs4
import collections
import random
import requests
import time
import datetime
import datetime_util as dt


class Error(Exception):
    pass


class ReserveAmericaParser(parser_base.Parser):

    def _FuzzySleep(self):
        sleep_time_secs = random.uniform(1.0, 5.0)
        self.logger.Log('Sleeping for %s...' % sleep_time_secs)
        time.sleep(sleep_time_secs)

    def _GetPostData(self, form_params, date):
        form_params = dict(form_params)
        form_params['campingDate'] = dt.FormatDate(date)
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
        element = cell.a if cell.a else cell
        return element.string and str(element.string).strip() == 'A'

    def _GetStatusCells(self, row):
        status_cells = row.find_all('td', class_='status')
        if not status_cells:
            raise Error('No status cells found in table.')
        return status_cells

    def _GetSiteName(self, row):
        site_name_tag = row.find(class_='siteListLabel')
        if not site_name_tag:
            raise Error('Could not find any html tag with class=siteListLabel')
        if not site_name_tag.a:
            raise Error('Could not "a" element inside site_name_tag')
        return str(site_name_tag.a.string).strip()

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

    def _GetAvailability(self, campsite, start_date, site_to_available_dates):
        """Gets availability on and 14 days after start date from reserveamerica for specified campsite.

        Doesn't return anything but updates the site_to_available_dates dict.
        """

        self.logger.Log('Getting availability data from start_date %s' % dt.FormatDate(start_date))
        session = requests.Session()

        self.logger.Log('Starting GET request to setup session cookies etc.')
        session.get(campsite.request_url)

        self.logger.Log('Starting POST request to retrieve 2 week availability data')
        response = session.post(campsite.request_url, data=self._GetPostData(campsite.form_params, start_date))

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

    def ParseAvailability(self, campsite, start_date, end_date):
        """Gets availability between start_date and end_date from reserveamerica for the specified campsite.

        Returns site_to_available_dates dict.
        """
        self.logger.Log('Retrieving availability from %s to %s' % (dt.FormatDate(start_date), dt.FormatDate(end_date)))
        site_to_available_dates = collections.defaultdict(list)
        while start_date < end_date:
            self._GetAvailability(campsite, start_date, site_to_available_dates)
             # Each self._GetAvailability call gets 14 days data so now we increment by 14
             # and loop again.
            start_date += datetime.timedelta(days=14)
            self._FuzzySleep()
        return site_to_available_dates

