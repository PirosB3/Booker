import datetime
import functools
import logging
import os
import pymongo
import re
import requests
import BeautifulSoup

from pymongo.uri_parser import parse_uri

ROOT_URL = 'https://upsu.sports-booker.com'
LOGIN_URL = '/login.php'
ORDER_URL = '/order.php'
CHECKOUT_URL = '/order_checkout.php'
WEEK_VIEW = '/index.php?atcid=110'

NEXT_DAY_RE = re.compile('value="Next Week &gt;" \/>" onclick="window\.location=\'(\/index.php\?showDate=\d+-\d+-\d+)\'" \/&gt;')

MY_TIMETABLE = {
    'Pilates': (
        ('Tue', '14:15:00'),
        ('Wed', '16:15:00'),
        ('Fri', '17:30:00')
    ),
}

logging.basicConfig(level=logging.INFO, format='[%(asctime)-15s %(module)s] %(message)s')
LOGGER = logging.getLogger(__name__) 
MONGO_URL = os.environ.get('MONGOHQ_URL', 'mongodb://localhost/booker')

USER_EMAIL = os.environ.get('USER_EMAIL')
USER_PASSWORD = os.environ.get('USER_PASSWORD')


class ExerciseClass(object):
    SESSION_DETAILS_RE = re.compile("getSessionDetails\('(\d+)','(\d+-\d+-\d+)\s(\d+:\d+:\d+)'")
    BACKGROUND_COLOR_RE = re.compile('background-color:\s(#\d+)')
    STRPTIME_STRING = '%Y-%m-%d %H:%M:%S'

    STATUS_BOOKED = 'booked'
    STATUS_STANDBY = 'standby'
    STATUS_FULL = 'full'
    STATUS_AVAILABLE = 'available'
    STATUS_UNAVAILABLE = 'unavailable'
    AVAILABILITY_MAP = {
        'btnCancelEdit'  :  STATUS_BOOKED,
        'btnStandbyOnly' :  STATUS_STANDBY,
        'btnFull'        :  STATUS_FULL,
        'btnBookNow'     :  STATUS_AVAILABLE
    }

    def __init__(self, node, name):
        self.name = name
        self.node = node
        self.id, self.date, self.time = self._set_id(node)
        self.status = self._get_availability(node)
        self.datetime = self._get_datetime(self.date, self.time)

    def get_meta_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'datetime': self.datetime,
            'status': self.status
        }

    def get_day(self):
        return self.datetime.strftime('%a')

    def _get_datetime(self, date, time):
        return datetime.datetime.strptime(' '.join([date, time]), self.STRPTIME_STRING)

    def _get_availability(self, node):
        for k, v in self.AVAILABILITY_MAP.iteritems():
            if node.find(attrs={'id': k}):
                return v
        return self.STATUS_UNAVAILABLE

    def _set_id(self, node):
        res = self.SESSION_DETAILS_RE.findall(str(node))
        if not res:
            raise Exception("Class details not found for: %s" % str(node))
        return res[0]
    
    def get_booking_id(self):
        return '%s|%s %s' % (self.id, self.date, self.time)


def main():
    if not MONGO_URL:
        LOGGER.error("MongoDB is not set up, so no data will be stored")
        raise Exception("Cannot run without Mongo")
    conn = pymongo.Connection(MONGO_URL)
    db = conn[parse_uri(MONGO_URL)['database']]
    persistence = db['bookings']

    LOGGER.info("*** Started booker ***")
    session = requests.Session()
    LOGGER.info("Logging in")
    session.post(''.join([ROOT_URL, LOGIN_URL]), data={ 'email': USER_EMAIL,
                                                'password': USER_PASSWORD })

    to_book = []

    # Get Day view
    current_path = WEEK_VIEW
    for _ in xrange(3):
        # build DOM
        current_url = ''.join([ROOT_URL, current_path])
        LOGGER.info("Reading: %s" % current_url)
        res = session.get(current_url)
        tree = BeautifulSoup.BeautifulSoup(res.text)

        # Get classes
        all_classes = tree.findAll(attrs={'class': 'calendar_list_session'})
        for class_name, timetable in MY_TIMETABLE.iteritems():
            schedule_for_class = filter(lambda c: c.find(text=class_name), all_classes)
            _ec = functools.partial(ExerciseClass, name=class_name)
            schedule_for_class = map(_ec, schedule_for_class)

            # Check if class should be booked
            for p in schedule_for_class:
                if (p.get_day(), p.time) in timetable:
                    LOGGER.info("[%s] class added for %s" % (class_name, p.time))
                    to_book.append(p)

        # Get next day button
        background = str(tree.find(attrs={'class': 'background'}))
        btn_next_re = NEXT_DAY_RE.findall(background)
        if btn_next_re:
            current_path = btn_next_re[0]

    # Iterate through classes and check if booking possible
    can_book = [ExerciseClass.STATUS_STANDBY, ExerciseClass.STATUS_AVAILABLE]
    for p in to_book:
        if p.status in can_book:
            LOGGER.info("[%s] booking class for %s" % (p.name, p.time))
            session.post(''.join([ROOT_URL, ORDER_URL]), {
                'areaActivitySessionId': p.get_booking_id()
            })
            res = session.post(''.join([ROOT_URL, CHECKOUT_URL]), data={
                "stageCheckout": "1",
                "paymentMethodId": "15",
                "transactionDescription": "Payment for order reference undefined",
                "totalCost": "0.00",
                "btnBookNow": "Book Now"
            })
            if 'Invalid' in res.url:
                LOGGER.error("[%s] class already booked or unavailable for %s" % (p.name, p.time))
            elif 'order_confirmation.php' in res.url:
                LOGGER.info("[%s] class was successfully booked for %s" % (p.name, p.time))
                persistence.insert(p.get_meta_data())


if __name__ == '__main__':
    main()
