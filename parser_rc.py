import bs4
import collections
import datetime
import random
import re
import requests
import time
import parser_base
import datetime_util as dt


NOT_AVAIL_REGEX = re.compile(r'^(\w+).*(\d{2}\/\d{2}\/\d{4}).*is not available$')
AVAIL_REGEX = re.compile(r'^(\w+).*is available on.*(\d{2}\/\d{2}\/\d{4})$')


class Error(Exception):
    pass


class ReserveCaliforniaParser(parser_base.Parser):

    def _FuzzySleep(self):
        sleep_time_secs = random.uniform(1.0, 5.0)
        self.logger.Log('Sleeping for %s...' % sleep_time_secs)
        time.sleep(sleep_time_secs)

    def _GetFieldValue(self, soup, field_id):
        field = soup.find(id=field_id)
        if field:
            return field.get('value')
        else:
            raise Error('No %s found', field_id)

    def _FormatDateForPost(self, date):
        return date.strftime(r'%m/%d/%Y')

    def _GetViewStateForPost(self, prev_response):
        """ReserveCa uses ASP.net which uses the concepts of VIEWSTATE.

        These are some encoding (perhaps encrypted) of some contextual form information
        from previous pages. VIEWSTATE and related fields are set in each page as hidden
        fields and are sent on all subsequent requests from the current page (as represented
        by prev_response). We read these hidden fields and then return them so that the caller
        can use them in subsequent POST requests.
        """
        soup = bs4.BeautifulSoup(prev_response.text, 'html5lib')
        self.logger.Log('Getting view_state ...')
        view_state = self._GetFieldValue(soup, '__VIEWSTATE')
        self.logger.Log('Getting view_state_generator ...')
        view_state_generator = self._GetFieldValue(soup, '__VIEWSTATEGENERATOR')
        return view_state, view_state_generator

    def _GetFirstPostData(self, campsite, prev_response, start_date):
        view_state, view_state_generator = self._GetViewStateForPost(prev_response)
        start_date_formatted = self._FormatDateForPost(start_date)
        form_params = {
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_state_generator,
            'ctl00$ctl00$AdvanceMainSearch$hdnAutoPlaceId': campsite.place_id,
            'ctl00$ctl00$mainContent$hdnsearchplaceid': campsite.place_id,
            'ctl00$ctl00$mainContent$hdnMasterPlaceId': campsite.place_id,
            'ctl00$ctl00$AdvanceMainSearch$hdncustomautocomplete':campsite.place_name,
            'ctl00$ctl00$mainContent$hdnSearchPlaceName': campsite.place_name,
            'ctl00$ctl00$mainContent$txtSearchparkautocomplete': campsite.place_name,
            'ctl00$ctl00$mainContent$txtSearchparkautocompletehearst': campsite.place_name,
            'ctl00$ctl00$mainContent$txtSearchparkautocompleteother': campsite.place_name,
            'ctl00$ctl00$AdvanceMainSearch$hdnArrivalDate': start_date_formatted,
            'ctl00$ctl00$AdvanceMainSearch$txtArrivalDate': start_date_formatted,
            'ctl00$ctl00$mainContent$txtArrivalDate': start_date_formatted,
            # pre-filled default valued fields.
            '__EVENTTARGET':'',
            '__EVENTARGUMENT':'',
            'ctl00$ctl00$hdnLoginCaptchResponse':'',
            'ctl00$ctl00$Hidscreenresolutionmain':'',
            'ctl00$ctl00$hdnCulture':'',
            'g-recaptcha-response':'',
            'ctl00$ctl00$txtCaptcha':'',
            'ctl00$ctl00$AdvanceMainSearch$hdnLat':'37.17159',
            'ctl00$ctl00$AdvanceMainSearch$hdnLag':'122.22203',
            'ctl00$ctl00$AdvanceMainSearch$hdnautocomplete':'',
            'ctl00$ctl00$AdvanceMainSearch$hdnNights':'0',
            'ctl00$ctl00$AdvanceMainSearch$ddlNights':'0',
            'ctl00$ctl00$AdvanceMainSearch$hdnEnableGoogleAnalyticCodeTracing':'',
            'ctl00$ctl00$mainContent$indexValue':'',
            'ctl00$ctl00$mainContent$ddlFacilityCategory':'1',
            'ctl00$ctl00$mainContent$hdnparksize':'Medium',
            'ctl00$ctl00$mainContent$hdnScreenresolution':'728',
            'ctl00$ctl00$mainContent$hdndefaultLat':'37.88904571533203',
            'ctl00$ctl00$mainContent$hdndefaultLag':'122.61078643798828',
            'ctl00$ctl00$mainContent$hdnIsAutocompleteFillHome':'1',
            'ctl00$ctl00$mainContent$hdnSearchtype':'Park',
            'ctl00$ctl00$mainContent$ddlHomeNights':'1',
            'ctl00$ctl00$mainContent$ddl_homeCategories':'0',
            'ctl00$ctl00$mainContent$ddl_homeCampingUnit':'0',
            'ctl00$ctl00$mainContent$ddl_homeLength':'0',
            'ctl00$ctl00$mainContent$hdnHomeUnitTypeCategory':'',
            'ctl00$ctl00$mainContent$TextBox1':'',
            'ctl00$ctl00$mainContent$TextBox2':'',
            'ctl00$ctl00$mainContent$btnSearch':'Go',
            'ctl00$ctl00$mainContent$homeContent$indexValue':'',
        }
        return form_params

    def _GetFinalPostData(self, campsite, prev_response, start_date):
        view_state, view_state_generator = self._GetViewStateForPost(prev_response)
        start_date_formatted = self._FormatDateForPost(start_date)
        form_params = {
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_state_generator,
            'ctl01$AdvanceMainSearch$hdnArrivalDate': start_date_formatted,
            'ctl01$AdvanceMainSearch$txtArrivalDate': start_date_formatted,
            'ctl01$mainContent$SearchUnitAvailbity$txtArrivalDate': start_date_formatted,
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdnArrivalDateSearchUnitAvailbity': start_date_formatted,
            'ctl01$mainContent$txtDateRange': start_date_formatted,
            'ctl01$mainContent$hdnPlaceid': campsite.place_id,
            'ctl01$mainContent$SearchUnitAvailbity$txtCityParkSearch': campsite.place_name,
            'ctl01$mainContent$hdnFacilityid': campsite.facility_id,
            'ctl01$mainContent$hdnFacilityType': campsite.facility_type,
            # pre-filled default valued fields.
            '__EVENTTARGET':'',
            '__EVENTARGUMENT':'',
            'ctl01$hdnLoginCaptchResponse':'',
            'ctl01$Hidscreenresolutionmain':'',
            'ctl01$hdnCulture':'',
            'g-recaptcha-response':'',
            'ctl01$txtCaptcha':'',
            'ctl01$AdvanceMainSearch$hdnAutoPlaceId':'',
            'ctl01$AdvanceMainSearch$hdnLat':'37.88904571533203',
            'ctl01$AdvanceMainSearch$hdnLag':'122.61078643798828',
            'ctl01$AdvanceMainSearch$hdnautocomplete':'',
            'ctl01$AdvanceMainSearch$hdncustomautocomplete':'',
            'ctl01$AdvanceMainSearch$hdnNights':'0',
            'ctl01$AdvanceMainSearch$ddlNights':'0',
            'ctl01$AdvanceMainSearch$hdnEnableGoogleAnalyticCodeTracing':'',
            'ctl01$mainContent$btngetFacilitiess':'Hure',
            'ctl01$mainContent$hdClient':'',
            'ctl01$mainContent$Hidscreenresolution':'',
            'ctl01$mainContent$hiddenPlaceLevel':'',
            'ctl01$mainContent$facilityChanged':'',
            'ctl01$mainContent$IsParkFeatures':'0',
            'ctl01$mainContent$hdnParkFirstBlockFullDesc':"",
            'ctl01$mainContent$hdnInventoryUpdateClick':'1',
            'ctl01$mainContent$SearchUnitAvailbity$hdnNightsSearchUnitAvailbity':'1',
            'ctl01$mainContent$SearchUnitAvailbity$hdnSearchtypeSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdnParkSizeSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdnSearchPlaceIdSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdnAutoPlaceIdSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdnLatSearchUnitAvailbity':'37.88904571533203',
            'ctl01$mainContent$SearchUnitAvailbity$hdnLagSearchUnitAvailbity':'122.61078643798828',
            'ctl01$mainContent$SearchUnitAvailbity$hdnautocompleteSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdncustomautocompleteSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdnIsPremiumSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdnIsAdaSearchUnitAvailbity':'0',
            'ctl01$mainContent$SearchUnitAvailbity$hdnIsPlaceSearchUnitAvailbity':'0',
            'ctl01$mainContent$SearchUnitAvailbity$hdnIsFacilityBacktoSearchUnitPlace':'0',
            'ctl01$mainContent$SearchUnitAvailbity$hdnParkFinderArray':'',
            'ctl01$mainContent$SearchUnitAvailbity$hdnIsAutocompleteFill':'1',
            'ctl01$mainContent$SearchUnitAvailbity$hdn_NewCampingUnitSearchUnitAvailbity':'0',
            'ctl01$mainContent$SearchUnitAvailbity$hdn_IsParkAllData':'false',
            'ctl01$mainContent$SearchUnitAvailbity$ddlNightsSearchUnitAvailbity':'1',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdn_CategoriesSearchUnitAvailbity':'0',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdn_CampingUnitSearchUnitAvailbity':'0',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdn_LengthSearchUnitAvailbity':'0',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdn_SelectCampingEquipSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdnddlLenghtSearchUnitAvailbity':'0',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdnLeft_placeidSearchUnitAvailbity':'',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$ddl_Categories':'0',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$ddl_CampingUnit':'0',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$ddl_Length':'0',
            'ctl01$mainContent$SearchUnitAvailabilityforPlace$hdnPlaceUnitTypeCategory':'',
            'ctl01$mainContent$facilitySearch$hdn_CategoriesSearchFacilityUnitAvailbity':'0',
            'ctl01$mainContent$facilitySearch$hdn_CampingUnitFacilitySearchUnitAvailbity':'0',
            'ctl01$mainContent$facilitySearch$hdn_LengthSearchUnitFacilityAvailbity':'0',
            'ctl01$mainContent$facilitySearch$hdnIsAdaSearchUnitfacility':'0',
            'ctl01$mainContent$facilitySearch$ddl_Categories_facility':'0',
            'ctl01$mainContent$facilitySearch$ddl_CampingUnit_facility':'0',
            'ctl01$mainContent$facilitySearch$ddl_Length_facility':'0',
            'ctl01$mainContent$facilitySearch$hdnFacilityUnitTypeCategory':'',
            'ctl01$mainContent$ugReservationGrid$hdnSelectedUnits':'',
            'ctl01$mainContent$ugReservationGrid$hdnnotavailableunit':'',
            'ctl01$mainContent$ugReservationGrid$hdnnotavailableunitAdvanced':'',
        }
        return form_params

    def _ValidateAndParse(self, cell):
        title = cell.get('title')
        if not title:
            return False, 'no title found on cell'
        result = NOT_AVAIL_REGEX.match(title)
        if result:
            is_available = False
        else:
            result = AVAIL_REGEX.match(title)
            if result:
                is_available = True
            else:
                return False, 'title "%s" did not match regex' % title

        # Determine sitname as string.
        site_name = result.groups()[0].strip()

        # Determine date as datetime.
        str_date = result.groups()[1].strip()
        date = datetime.datetime.strptime(str_date, r'%m/%d/%Y')

        return True, (site_name, date, is_available)

    def _GetAvailability(self, campsite, start_date, site_to_available_dates):
        """Gets availability on and 14 days after start date from reserveamerica for specified campsite.

        Doesn't return anything but updates the site_to_available_dates dict.
        """
        self.logger.Log('Getting availability data from start_date %s' % dt.FormatDate(start_date))
        session = requests.Session()

        self.logger.Log('Starting GET request to setup session cookies etc.')
        first_response = session.get('https://www.reservecalifornia.com')

        if first_response.status_code != 200:
            raise Error('Receive http code %s instead of 200' % first_response.status_code)

        # This first POST request doesn't get us the results but sets up context for the final
        # subsequent request. In addition this POST request actually gets redirected to a GET request.
        self.logger.Log('Starting first POST request to set up context for specific park')
        second_response = session.post(
            'https://www.reservecalifornia.com/CaliforniaWebHome/',
            data=self._GetFirstPostData(campsite, first_response, start_date))

        if second_response.status_code != 200:
            raise Error('Receive http code %s instead of 200' % second_response.status_code)

        # Final POST request which will get us all the availability data.
        self.logger.Log('Starting final POST request to retrieve availability data')
        final_response = session.post(
            'https://www.reservecalifornia.com/CaliforniaWebHome/Facilities/SearchViewUnitAvailabity.aspx',
            data=self._GetFinalPostData(campsite, second_response, start_date))

        if final_response.status_code != 200:
            raise Error('Receive http code %s instead of 200' % final_response.status_code)

        self.logger.Log('Parsing response')
        soup = bs4.BeautifulSoup(final_response.text, 'html5lib')

        self.logger.Log('Retrieving all cells from html')
        cells = soup.find_all('td')

        self.logger.Log('Processing %s cells' % len(cells))
        for cell in cells:
            is_valid, invalid_reason_or_parsed_result = self._ValidateAndParse(cell)
            if not is_valid:
                reason = invalid_reason_or_parsed_result
                self.logger.Log('Found invalid cell because %s ...' % reason)
                continue

            self.logger.Log('Found valid cell ...')
            parsed_result = invalid_reason_or_parsed_result
            site, date, is_available = parsed_result
            self.logger.Log('Site: %s, date: %s, is_available: %s' % (site, date, is_available))
            if is_available:
                site_to_available_dates[site].append(date)
        self.logger.Log('Finished processing row')


    def ParseAvailability(self, campsite, start_date, end_date):
        """Gets availability between start_date and end_date from reserveamerica for the specified campsite.

        Returns site_to_available_dates dict.
        """
        self.logger.Log('Retrieving availability from %s to %s' % (dt.FormatDate(start_date), dt.FormatDate(end_date)))
        site_to_available_dates = collections.defaultdict(list)
        while start_date < end_date:
            self._GetAvailability(campsite, start_date, site_to_available_dates)
             # Each self._GetAvailability call gets 20 days data so now we increment by 21
             # and loop again.
            start_date += datetime.timedelta(days=21)
            self._FuzzySleep()
        return site_to_available_dates

