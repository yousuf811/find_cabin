"""List of Campsites that we support searching for.

The top base class is Campsite. Each class represents a specific campsite with appropriate information
that can be used by parsers to scrape information about that campsite.

"""
import re

class Campsite(object):
    """A generic base class for Campsite information.

    Subclasses should have the following attributes:
     - name
     - site_regex
    """

    @classmethod
    def Validate(cls):
        if not hasattr(cls, 'name'):
            return False, 'name static attribute not found on Campsite class: %s' % cls.__name__
        if not hasattr(cls, 'site_regex'):
            return False, 'site_regex static attribute not found on Campsite class: %s' % cls.__name__
        return True, None


class ReserveAmericaCampsite(Campsite):
    """Base class for all ReserveAmerica based campsites.

    Subclasses should have the following attributes:
     - request_url
     - form_params
    """
    @classmethod
    def Validate(cls):
        is_valid, err_msg = super(ReserveAmericaCampsite, cls).Validate()
        if not is_valid:
            return False, err_msg
        if not hasattr(cls, 'request_url'):
            return False, 'request_url static attribute not found on campsite class: %s' % cls.__name__
        if not hasattr(cls, 'form_params'):
            return False, 'form_params static attribute not found on campsite class: %s' % cls.__name__
        return True, None

    @staticmethod
    def MergeFormParams(campsite_form_params):
        base_form_params = {
            'contractCode': 'CA',
            'parkId': '120063',
            'siteTypeFilter': 'ALL',
            'availStatus': '',
            'submitSiteForm': 'true',
            'search': 'site',
            'lengthOfStay': '1',
            'campingDateFlex': '2w',
            'currentMaximumWindow': '12',
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
            'camping_3102_3012': '',
        }
        new_form_params = base_form_params.copy()
        new_form_params.update(campsite_form_params)
        return new_form_params


class ReserveCaliforniaCampsite(Campsite):
    """Base class for all ReserveCalifornia based campsites.

    Subclasses should have the following attributes:
     - place_id
     - place_name
     - facility_id
     - facility_type
    """

    @classmethod
    def Validate(cls):
        is_valid, err_msg = super(ReserveCaliforniaCampsite, cls).Validate()
        if not is_valid:
            return False, err_msg
        if not hasattr(cls, 'place_id'):
            return False, 'place_id static attribute not found on campsite class: %s' % cls.__name__
        if not hasattr(cls, 'place_name'):
            return False, 'place_name static attribute not found on campsite class: %s' % cls.__name__
        if not hasattr(cls, 'facility_id'):
            return False, 'facility_id static attribute not found on campsite class: %s' % cls.__name__
        if not hasattr(cls, 'facility_type'):
            return False, 'facility_type static attribute not found on campsite class: %s' % cls.__name__
        return True, None


# Campsite class for Steep Ravine cabins.
class SteepRavine(ReserveCaliforniaCampsite):
    name = 'Steep Ravine'
    site_regex = re.compile(r'CB.*')
    place_id = '682'
    place_name = 'Mount Tamalpais SP'
    facility_id = '766'
    facility_type = '0'


# NO LONGER WORKS ON RESERVERAMERICA, HAS MOVED TO RECREATION.GOV
# Campsite class for black mountain lookout.
class BlackMountainLookout(ReserveAmericaCampsite):
    name = 'Black Mountain Lookout'
    site_regex = re.compile(r'.*')
    request_url = 'https://www.reserveamerica.com/camping/black-mountain-lookout/r/campgroundDetails.do?contractCode=NRSO&parkId=72306'
    form_params = ReserveAmericaCampsite.MergeFormParams({
        'contractCode': 'NRSO',
        'parkId': '72306',
        'contractDefaultMaxWindow': 'MS:24,LT:18,GA:24,SC:13',
        'stateDefaultMaxWindow': 'MS:24,GA:24,SC:13',
    })


class RedwoodRegionalPark(ReserveAmericaCampsite):
    name = 'Redwood Regional Park'
    site_regex = re.compile(r'.*')
    request_url = 'https://www.reserveamerica.com/camping/redwood-regional-park/r/campgroundDetails.do?contractCode=EB&parkId=110458'
    form_params = ReserveAmericaCampsite.MergeFormParams({
        'contractCode': 'EB',
        'parkId': '110458',
        'contractDefaultMaxWindow': 'MS:24,LT:18,GA:24,SC:13,PA:24,LARC:24,CTLN:13,LA:13,PRCG:13',
        'stateDefaultMaxWindow': 'MS:24,GA:24,PA:24,CO:24,CA:13,LA:13,TX:13,FL:13,WA:13,NY:13,SC:13,WI:13,MA:13,ME:13,OH:13,GA:13,ID:13,MI:13,CA:13,UT:13,MN:13,MO:13,WY:13,OR:13,IL:13,IN:13,MS:13,MT:13,VA:13,AL:13,CO:13,KY:13,CT:13,PA:13,AR:13,LA:13,NC:13,NE:13,TN:13,NJ:13,NM:13',
    })


