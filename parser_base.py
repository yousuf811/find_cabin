"""A Parser base class that encapsulates functionality to scrape HTML for
a specific campsite and time range."""

class Parser(object):

    def __init__(self, logger):
        self.logger = logger

    def ParseAvailability(self, campsite, start_date, end_date):
        raise NotImplementedError
