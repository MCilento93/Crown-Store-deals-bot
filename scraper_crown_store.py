### IMPORTING
#import aiohttp, asyncio
import requests
from bs4 import BeautifulSoup

### GLOBALS
URL_SPECIAL_OFFERS = 'https://www.elderscrollsonline.com/en-us/crownstore/category/36'
URL_FEATURED = 'https://www.elderscrollsonline.com/en-us/crownstore'
URL_ESOP_DEALS = 'https://www.elderscrollsonline.com/en-us/crownstore/eso-plus'

### FUNCTIONS
#async def get_html(url):
#  async with aiohttp.ClientSession() as session:
#    async with session.get(url) as response:
#      html = await response.text()
#  return html


def get_html(url):
  return requests.get(url).content


def remove_duplicates(item_list):
  return [dict(t) for t in {tuple(d.items()) for d in item_list}]


def scrape(html):
  # Opening the soup
  soup = BeautifulSoup(html, 'html.parser')

  # Get items
  crown_items = soup.find_all("crown-item")
  item_list = []
  for item in crown_items:

    # Parse title
    title = item.h4.find(class_='crown-title').text.strip()
    # print(f'scraping: {title}')

    # Parse time left
    if item.h4.find(class_='time-left'):
      time_left = item.find(class_='time-left').text.strip().replace(
          'Time Remaining', '')
    else:
      time_left = None

    # Parse link
    link = 'https://www.elderscrollsonline.com' + item.a['href']

    # Parse cost
    if item.find(class_='eso-plus-label'):
      # CASE 1: there are either a cost in crowns or a deal for eso+ subscribers
      _costs_crowns = item.find(class_='crowns-price').find_all(
          class_='sr-only')
      cost_crowns = _costs_crowns[0].text.strip()
      if cost_crowns:
        cost_esop_crowns = _costs_crowns[1].text.strip()
      else:
        cost_esop_crowns = 'FREE!'
      cost_gems = None
      cost_seals = None
    elif item.find(class_='gems-price'):
      # CASE 2: there are either cost in gems or seals
      cost_crowns = None
      cost_esop_crowns = None
      cost_gems = item.find(class_='gems-price').find(
          class_='sr-only').text.strip()
      cost_seals = item.find(class_='seals-price').find(
          class_='sr-only').text.strip()
    elif item.find(class_='crowns-price').find(class_='sr-only'):
      # CASE 3: only crown cost
      cost_crowns = item.find(class_='crowns-price').find(
          class_='sr-only').text.strip()
      cost_esop_crowns = None
      cost_gems = None
      cost_seals = None
    else:
      # CASE 4: no cost
      cost_crowns = 'FREE!'
      cost_esop_crowns = None
      cost_gems = None
      cost_seals = None

    # Packing everything up
    item_list += [{
        'item_title': title,
        'item_link': link,
        'item_time_left': time_left,
        'item_cost_crowns': cost_crowns,
        'item_cost_esop_crowns': cost_esop_crowns,
        'item_cost_gems': cost_gems,
        'item_cost_seals': cost_seals
    }]

  # Remove duplicates
  return remove_duplicates(item_list)


class ScrapedCategory():

  def __init__(self, category):

    if category == 'special_offers':
      self.html = get_html(URL_SPECIAL_OFFERS)
      self.list = scrape(self.html)
      self.header = 'Special offers'
    elif category == 'featured':
      self.html = get_html(URL_FEATURED)
      self.list = scrape(self.html)
      self.header = 'Featured'
    elif category == 'esop_deals':
      self.html = get_html(URL_ESOP_DEALS)
      self.list = scrape(self.html)
      self.header = 'ESO+ deals'

  @property
  def markdown(self):

    # Build row
    _list = []
    for i in self.list:
      _row = f"[{i['item_title']}](<{i['item_link']}>)"
      if i['item_cost_esop_crowns']:
        if i['item_cost_crowns']:
          _row += f" - {i['item_cost_crowns']}, 🏆 {i['item_cost_esop_crowns']}"
        else:  # free items in "eso+ deals"
          _row += f" - 🏆 {i['item_cost_esop_crowns']}"
      elif i['item_cost_gems']:
        _row += f" - {i['item_cost_gems']} or {i['item_cost_seals']}"
      else:
        _row += f" - {i['item_cost_crowns']}"

      if i['item_time_left']:
        _row += f" ({i['item_time_left']})"
      _list += [_row]

    list_str = '\n'.join(_list)

    # Build final markup
    markdown = f"""
**💸 {self.header} ({len(self.list)})**
{list_str}
""".replace(' Crowns', '👑').replace(' Crown Gems', '💎').replace('(0 day left)','(expiring today)')
    return markdown


def move_from_featured_to_esop(featured: ScrapedCategory,
                               esop_deals: ScrapedCategory):
  for i in featured.list:
    if i['item_cost_esop_crowns']:
      # move this element from featured to eso+ deals
      esop_deals.list += [i]
      featured.list.remove(i)
    esop_deals.list = remove_duplicates(esop_deals.list)
  return featured, esop_deals


### MAIN
if __name__ == '__main__':

  # Special offers
  special_offers = ScrapedCategory('special_offers')

  # Featured
  featured = ScrapedCategory('featured')

  # ESO+ deals
  esop_deals = ScrapedCategory('esop_deals')

  # correct elements
  featured, esop_deals = move_from_featured_to_esop(featured, esop_deals)
