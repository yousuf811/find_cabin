# List of Campsites we support.
import re

def MergeBaseFormParams(campsite_form_params):
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

# Campsite class for Steep Ravine cabins.
class SteepRavine(object):
    name = 'Steep Ravine'
    request_url = 'https://www.reserveamerica.com/camping/mount-tamalpais-sp/r/campgroundDetails.do?contractCode=CA&parkId=120063'
    form_params = MergeBaseFormParams({
        'contractCode': 'CA',
        'parkId': '120063',
        'contractDefaultMaxWindow': 'MS:24,LT:18,GA:24,SC:13,PA:24,LARC:24',
        'stateDefaultMaxWindow': 'MS:24,GA:24,SC:13,PA:24,CO:24',
    })
    site_regex = re.compile(r'CB.*')


# Campsite class for black mountain lookout.
class BlackMountainLookout(object):
    name = 'Black Mountain Lookout'
    request_url = 'https://www.reserveamerica.com/camping/black-mountain-lookout/r/campgroundDetails.do?contractCode=NRSO&parkId=72306'
    form_params = MergeBaseFormParams({
        'contractCode': 'NRSO',
        'parkId': '72306',
        'contractDefaultMaxWindow': 'MS:24,LT:18,GA:24,SC:13',
        'stateDefaultMaxWindow': 'MS:24,GA:24,SC:13',
    })
    site_regex = re.compile(r'.*')
