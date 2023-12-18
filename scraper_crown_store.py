### IMPORTING
#import aiohttp, asyncio
import requests
from bs4 import BeautifulSoup

### GLOBALS
URL_SPECIAL_OFFERS = 'https://www.elderscrollsonline.com/en-us/crownstore/category/36'
URL_FEATURED = 'https://www.elderscrollsonline.com/en-us/crownstore'

### FUNCTIONS
#async def get_html(url):
#  async with aiohttp.ClientSession() as session:
#    async with session.get(url) as response:
#      html = await response.text()
#  return html


def get_html(url):
  return requests.get(url).content


def scrape_special_offers(html):

  # Opening the soup
  soup = BeautifulSoup(html, 'html.parser')

  # Get items
  crown_items = soup.find_all("crown-item")
  special_offers_list = []
  for item in crown_items:
    # Parse title
    title = item.h4.find(class_='crown-title').text.strip()

    # Parse time left
    if item.h4.find(class_='time-left'):
      time_left = item.find(class_='time-left').text.strip().replace(
          'Time Remaining', '')
    else:
      time_left = None

    # Parse link
    link = 'https://www.elderscrollsonline.com' + item.a['href']

    # Parse cost
    cost = item.find(class_='crowns-price').find(class_='sr-only').text.strip()

    # Packing everything up
    special_offers_list += [{
        'item_title': title,
        'item_time_left': time_left,
        'item_cost': cost,
        'item_link': link,
    }]

  # Remove duplicates
  special_offers_list = [
      dict(t) for t in {tuple(d.items())
                        for d in special_offers_list}
  ]

  # Build row "Special offers"
  _list = []
  for i in special_offers_list:
    _row = f"[{i['item_title']}](<{i['item_link']}>) - {i['item_cost']}"
    if i['item_time_left']:
      _row += f" ({i['item_time_left']})"
    _list += [_row]
  special_offers_list_str = '\n'.join(_list)

  # Build final markup
  markup = f"""
**💸 Special offers ({len(special_offers_list)})**
{special_offers_list_str}
""".replace(' Crowns', '👑')
  return markup, special_offers_list


def scrape_featured(html):

  # Opening the soup
  soup = BeautifulSoup(html, 'html.parser')

  # Get items
  crown_items = soup.find_all("crown-item")
  featured_list = []
  for item in crown_items:
    # Parse title
    title = item.h4.find(class_='crown-title').text.strip()

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
      cost_esop_crowns = _costs_crowns[1].text.strip()
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
    else:
      # CASE 3: only crown cost
      cost_crowns = item.find(class_='crowns-price').find(
          class_='sr-only').text.strip()
      cost_esop_crowns = None
      cost_gems = None
      cost_seals = None

    # Packing everything up
    featured_list += [{
        'item_title': title,
        'item_link': link,
        'item_time_left': time_left,
        'item_cost_crowns': cost_crowns,
        'item_cost_esop_crowns': cost_esop_crowns,
        'item_cost_gems': cost_gems,
        'item_cost_seals': cost_seals,
    }]

  # Remove duplicates
  featured_list = [dict(t) for t in {tuple(d.items()) for d in featured_list}]

  # Build row "Featured"
  _list = []
  for i in featured_list:
    _row = f"[{i['item_title']}](<{i['item_link']}>)"
    if i['item_cost_esop_crowns']:
      _row += f" - {i['item_cost_crowns']}, 🏆 {i['item_cost_esop_crowns']}"
    elif i['item_cost_gems']:
      _row += f" - {i['item_cost_gems']} or {i['item_cost_seals']}"
    else:
      _row += f" - {i['item_cost_crowns']}"

    if i['item_time_left']:
      _row += f" ({i['item_time_left']})"
    _list += [_row]
  featured_list_str = '\n'.join(_list)

  # Build final markup
  markup = f"""
**💸 Featured ({len(featured_list)})**
{featured_list_str}
""".replace(' Crowns', '👑').replace(' Crown Gems', '💎')
  return markup, featured_list


### MAIN
if __name__ == '__main__':

  # Special offers
  #html = asyncio.run(get_html(URL_SPECIAL_OFFERS))
  html= get_html(URL_SPECIAL_OFFERS)
  special_offers = scrape_special_offers(html)
  print(special_offers[0])

  # Featured
  # html = asyncio.run(get_html(URL_FEATURED))
  html= get_html(URL_FEATURED)
  featured = scrape_featured(html)
  print(featured[0])
