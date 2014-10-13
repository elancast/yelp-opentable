import json
import oauth2
import termcolor
import threading
import urllib2

CONSUMER_KEY = '8JdpxLL5e9we__fElm1j0g'
CONSUMER_SECRET = 'Nw7443fMf6vAvGKiWfsCsuy7eWc'
TOKEN = '4FRwolTY8Dg26b140kbkrBDic_r2HBps'
TOKEN_SECRET = '4h6AAcM9umbmDAwR4hbzOCu2-aE'

URL = 'http://api.yelp.com/v2/search'

class YelpCaller(threading.Thread):
  def __init__(self, restaurant, neighborhood, destination = []):
    self._url = self._get_url(restaurant, neighborhood)
    self._destination = destination;
    threading.Thread.__init__(self)

  def _get_url(self, restaurant, neighborhood, limit=1):
    if not 'San' in neighborhood:
      neighborhood += ', San Francisco, CA'

    oauth_request = oauth2.Request('GET', URL, {})
    data = {
      'term': restaurant,
      'location': neighborhood,
      'limit': 1,
      'oauth_nonce': oauth2.generate_nonce(),
      'oauth_timestamp': oauth2.generate_timestamp(),
      'oauth_token': TOKEN,
      'oauth_consumer_key': CONSUMER_KEY
      }
    oauth_request.update(data)

    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    token = oauth2.Token(TOKEN, TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(),
                               consumer,
                               token)
    return oauth_request.to_url()

  def get_data(self):
    resp = urllib2.urlopen(self._url)
    s = resp.read()
    resp.close()

    data = json.loads(s)
    return YelpBusiness(data)

  def run(self):
    print 'go'
    business = self.get_data()
    self._destination.append(business)
    print 'onde'

class YelpBusiness:
  def __init__(self, search_data):
    businesses = search_data['businesses']
    if len(businesses) == 0:
      raise Error('No businesses found')

    # Trust yelp's ranking and take the first
    business = businesses[0]
    self.name = business['name']
    self.url = business['url']
    self.review_count = business['review_count']
    self.rating = business['rating']

    # Yelp gives a list of categories - stringify them
    categories = map(lambda item: item[0], business['categories'])
    self.category = ', '.join(categories)

  def get_rating(self):
    rating = '%.1f by %4d reviews' % (self.rating, self.review_count)
    return termcolor.colored(rating, self._get_color())

  def _get_color(self):
    if self.rating >= 4.3: return 'cyan'
    if self.rating >= 3.9: return 'green'
    if self.rating >= 3.3: return 'magenta'
    if self.rating >= 2.9: return 'yellow'
    return 'red'

  def __str__(self):
    return '%s\t%s\t%.1f\t%d\t%s' % (self.name, self.category, self.rating,
                                     self.review_count, self.url)

  def __eq__(self, other):
    return other != None and self.name == other.name

  def __ne__(self, other):
    return other == None or self.name != other.name

  def __lt__(self, other):
    if self.rating == other.rating:
      return self.review_count < other.review_count
    return self.rating < other.rating

  def __le__(self, other):
    if self.rating == other.rating:
      return self.review_count <= other.review_count
    return self.rating <= other.rating

  def __gt__(self, other):
    if self.rating == other.rating:
      return self.review_count > other.review_count
    return self.rating > other.rating

  def __ge__(self, other):
    if self.rating == other.rating:
      return self.review_count >= other.review_count
    return self.rating >= other.rating

def main():
  import sys
  if len(sys.argv) < 3:
    print 'USAGE: python %s <name of restaurant> <neighborhood>' % sys.argv[0]
    sys.exit(0)

  results = []
  caller = YelpCaller(sys.argv[1], sys.argv[2], results)
  caller.start()
  while caller.is_alive():
    import time; time.sleep(1)
  print '\n'.join(map(lambda i: str(i), results))

if __name__ == '__main__':
  main()
