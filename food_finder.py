import datetime
import json
import Queue
import sys
import termcolor
import threading
import urllib2

from yelp_caller import YelpCaller

MAX_RESULTS = 100
NUM_THREADS = 20
URL = "http://www.opentable.com/s/api?metroid=4&regionids=5&showmap=false&popularityalgorithm=NameSearches&sort=Name&excludefields=Description"

def lenify(s, l):
  if len(s) > l:
    return s[:l]
  else:
    return s + ''.join([' ' for i in range(l - len(s))])

def worker(queue):
  while True:
    biz = queue.get()
    biz.link_to_yelp()
    queue.task_done()

def kill_unicode(s):
  try:
    if not isinstance(s, unicode):
      s = unicode(s, 'utf-8')
    s = s.replace(u'\xe9', 'e')
    s = s.replace(u'\u2013', '-')
    s = s.replace(u'\xf1', 'n')
    s = s.replace(u'\xe4', 'a')
    s = s.replace(u'\xed', 'i')
    s = s.replace(u'\xe7', 'c')
    s = s.replace(u'\xf3', 'o')
    s = s.replace(u'\xe8', 'e')
    s = s.replace(u'\xe0', 'a')
    return s.encode('ascii')
  except:
    print s
    import pdb; pdb.set_trace()
    return s

def dateify(time_str):
  colon = time_str.find(':')
  hrs = time_str[:colon]
  mins = time_str[colon + 1:]
  if ' ' in mins:
    mins = mins[:mins.find(' ')]
  return datetime.datetime(2014, 1, 10, int(hrs), int(mins))

SECS_IN_DAY = 24 * 60 * 60
def diff_dates(a, b):
  val = (a - b).seconds
  return min(SECS_IN_DAY - val, val) / 60

class FoodFinder:
  def __init__(self, date, party_size):
    self._available = []

    date = urllib2.quote(date)
    self._url = '%s&covers=%d&datetime=%s' % (URL, party_size, date)

  def _fill_opentable(self):
    resp = urllib2.urlopen(self._url)
    s = resp.read()
    resp.close()
    return json.loads(s)['Results']['Restaurants']

  def go(self):
    options = self._fill_opentable()
    print '=== %d options ===\n' % len(options)

    threads = []
    queue = Queue.Queue()
    for i in range(NUM_THREADS):
      t = threading.Thread(target=worker, args=(queue,))
      t.daemon = True
      t.start()
      threads.append(t)

    businesses = map(lambda option: OpenTableBusiness(option), options)
    for business in businesses:
      queue.put(business)
    queue.join()

    businesses = self._sort_and_filter(businesses)
    for business in businesses:
      print business
      print ''

  def _sort_and_filter(self, businesses):
    businesses = sorted(businesses)
    return businesses
  """
    above = 4.1
    top = filter(lambda b: b.yelp.rating > above, businesses)
    while len(top) < MAX_RESULTS:
      above -= .5
      top = filter(lambda b: b.yelp.rating > above, businesses)

    return top
  """


class OpenTableBusiness:
  def __init__(self, data):
    self.neighborhood = data['Location']
    self.name = kill_unicode(data['Name'])
    self.time_slots = map(lambda i: ReservationTime(i), data['TimeSlots'])
    self.yelp = None

  def __str__(self):
    assert self.yelp != None

    availability = '  '.join(map(lambda i: str(i), self.time_slots))
    name = lenify(kill_unicode(self.yelp.name), 40)
    rating = self.yelp.get_rating()

    # Name     Stars by Count      Availability
    # Location, Type, URL
    return '%s  %s        %s\n%s  |  %s  |  %s' % \
        (name, rating, availability,
         lenify(self.neighborhood, 20),
         lenify(self.yelp.category, 40),
         self.yelp.url)

  def link_to_yelp(self):
    business = YelpCaller(self.name, self.neighborhood).get_data()
    self.yelp = business

  def __eq__(self, other):
    return other != None and self.name == other.name
  def __ne__(self, other):
    return other == None or self.name != other.name
  def __lt__(self, other):
    return self.yelp < other.yelp
  def __le__(self, other):
    return self.yelp <= other.yelp
  def __gt__(self, other):
    return self.yelp > other.yelp
  def __ge__(self, other):
    return self.yelp >= other.yelp

class ReservationTime:
  def __init__(self, data):
    self.is_available = data['IsAvail']
    self.time = data['TimeString'].replace(' PM', '').replace(' AM', '')

  def __str__(self):
    display = self.time if self.is_available else 'N/A'
    while len(display) < 5:
      display = ' ' + display
    return termcolor.colored(display, self._get_color())

  def _get_color(self):
    if not self.is_available: return 'magenta'
    global requested_time
    if self.time in requested_time: return 'green'

    diff = self._get_mins_from_requested()
    if diff < .5: return 'green'
    if diff < 1.5: return 'yellow'
    return 'red'

  def _get_mins_from_requested(self):
    global requested_time_datetime
    date = dateify(self.time)
    return diff_dates(date, requested_time_datetime) / 60.0

if len(sys.argv) < 4:
  print 'USAGE: python %s <date (10/12/2014)> <time (7:00)> <party size>' % \
      (sys.argv[0])
  sys.exit(0)

requested_date = sys.argv[1]
requested_time = sys.argv[2]
requested_size = sys.argv[3]

# Time should be: 07:00 PM
if not ':' in requested_time:
  requested_time = requested_time + ':00'
if not 'AM' in requested_time and not 'PM' in requested_time:
  requested_time = requested_time + ' PM'
if requested_time.find(':') < 2:
  requested_time = '0' + requested_time

# For coloring...
requested_time_datetime = dateify(requested_time)

# Date sohuld be: 10/12/2014
if not '/201' in requested_date:
  requested_date += '/2014'

requested_datetime = requested_date + ' ' + requested_time
print 'Finding for a party of %s at %s...\n' % \
    (requested_size, requested_datetime)
ff = FoodFinder(requested_datetime, int(requested_size))
ff.go()
