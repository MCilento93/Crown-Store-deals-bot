

### IMPORTING
import requests
from bs4 import BeautifulSoup


### GLOBALS
URL_SPECIAL_OFFERS = 'https://www.elderscrollsonline.com/en-us/crownstore/category/36'
URL_FEATURED = 'https://www.elderscrollsonline.com/en-us/crownstore'
URL_ESOP_DEALS = 'https://www.elderscrollsonline.com/en-us/crownstore/eso-plus'
DESIRED_ITEMS = """dlc
Orsinium
Guilds and Glory: The 4-DLC Mega-Pack
Thieves Guild
Dark Brotherhood
Shadows of the Hist
Horns of the Reach
The Clockwork City
Dragon Bones
Wolfhunter
Murkmire
Wrathstone
Summerset
Scalebreaker
Dragonhold
Harrowstorm
Elsweyr
Stonethorn
Markarth
Flames of Ambition
Greymoor
Year Two Mega-Pack: DLC Bundle
Season of the Dragon: DLC Bundle
Waking Flame
Deadlands
Ascending Tide
Blackwood
Year Three Mega-Pack: DLC Bundle
Lost Depths
Firesong
Dark Heart of Skyrim: DLC Bundle
Gates of Oblivion: DLC Bundle
Scribes of Fate
High Isle""".lower().split('\n')


### FUNCTIONS
def get_html(url):
    return requests.get(url).content

def scrape(html):
    # Opening the soup
    soup = BeautifulSoup(html, 'html.parser')

    # Get items
    crown_items = soup.find_all("crown-item")
    item_list = []
    for item in crown_items:

        # Parse title
        title = item.h4.find(class_='crown-title').text.strip()

        # Parse time left
        if item.h4.find(class_='time-left'):
            time_left = item.find(class_='time-left').text.strip().replace('Time Remaining', '')
        else:
            time_left = None

        # Parse link
        link = 'https://www.elderscrollsonline.com' + item.a['href']

        # Parse cost
        if item.find(class_='eso-plus-label'):
        # CASE 1: there are either a cost in crowns or a deal for eso+ subscribers
            _costs_crowns = item.find(class_='crowns-price').find_all(class_='sr-only')
            cost_crowns = _costs_crowns[0].text.strip()
            if cost_crowns:
                if len(_costs_crowns)>1:
                    cost_esop_crowns = _costs_crowns[1].text.strip()
                else:
                    cost_esop_crowns = 'EXCLUSIVE!'
            else:
                cost_esop_crowns = 'FREE!'
            cost_gems = None
            cost_seals = None
        elif item.find(class_='gems-price'):
        # CASE 2: there are either cost in gems or seals
            cost_crowns = None
            cost_esop_crowns = None
            cost_gems = item.find(class_='gems-price').find(class_='sr-only').text.strip()
            cost_seals = item.find(class_='seals-price').find(class_='sr-only').text.strip()
        elif item.find(class_='crowns-price').find(class_='sr-only'):
        # CASE 3: only crown cost
          cost_crowns = item.find(class_='crowns-price').find(class_='sr-only').text.strip()
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

    return item_list


### CLASSES
class ScrapedCategory():

    def __init__(self, category):
        # Import category Special offers
        if category == 'special_offers':
            self.html = get_html(URL_SPECIAL_OFFERS)
            self.list = scrape(self.html)
            self.header = 'Special offers'
        # Import category Featured
        elif category == 'featured':
            self.html = get_html(URL_FEATURED)
            self.list = scrape(self.html)
            self.header = 'Featured'
        # Import catgeory ESO Plus Deals
        elif category == 'esop_deals':
            self.html = get_html(URL_ESOP_DEALS)
            self.list = scrape(self.html)
            self.header = 'ESO+ deals'
        # Build bot-selection category
        elif category == 'best_deals':
            self.header = 'Best deals'
            self._special_offers = ScrapedCategory('special_offers')
            self._featured = ScrapedCategory('featured')
            self._esop_deals = ScrapedCategory('esop_deals')
            super_list = self._special_offers.list + self._featured.list + self._esop_deals.list
            self.list = []
            for i in super_list:
                accept_item = False
    
                # Acceptance criteria 1: it's amid the desired items
                if i['item_title'].lower() in DESIRED_ITEMS:
                    accept_item = True
    
                # Acceptance criteria 2: item is on sale
                if i['item_cost_crowns']:
                    if ' Sale Price' in i['item_cost_crowns']:
                        accept_item = True
                # Acceptance criteria 3: item is free
                    if 'FREE' in i['item_cost_crowns']:
                        accept_item = True
    
                # Acceptance criteria 4: item is in sale for eso+ owners
                if i['item_cost_esop_crowns']:
                    accept_item = True
    
                if accept_item:
                    self.list += [i]
        # Remove duplicates in the final instance according to a key
        self.remove_duplicates()
        self.sort_list()
        
    def sort_list(self):
        self.list = sorted(self.list, key=lambda d: d['item_title']) 
        
    def remove_duplicates(self, key='item_link'):
        keys_set = set()
        result = []
        for _dict in self.list:
            _value = _dict[key]
            if _value not in keys_set:
                keys_set.add(_value)
                result.append(_dict)
        self.list = result

    @property
    def title(self):
        return f"""**💸 {self.header} ({len(self.list)})**"""

    @property
    def markdown(self):
        markdown = f"""
**💸 {self.header} ({len(self.list)})**{self.markdown_no_title}
"""
        return markdown
        
    @property
    def markdown_no_title(self):
        
        def apply_markdown_cost(string):
            return string.replace(' Crowns', '👑').replace(' Crown Gems', '💎').replace(' Sale Price','👑 Sale Price')
        
        def apply_markdown_exp(string):
            return string.replace('(0 day left)', '(expiring today)')
        
        # No items in the category
        if self.list == []:
            return "\n🤷 No items today, sorry"
        
        # Build row
        _list = []
        for i in self.list:

            # Title
            if i['item_title'].lower() in DESIRED_ITEMS:
                _row = f"[**{i['item_title']}**](<{i['item_link']}>)" # bold if there are dlcs
            else:
                _row = f"[{i['item_title']}](<{i['item_link']}>)"

            # Cost
            if i['item_cost_esop_crowns']:
                if i['item_cost_crowns']:
                    _row += apply_markdown_cost(f" {i['item_cost_crowns']}, 🏆 {i['item_cost_esop_crowns']}")
                else:  # free items in "eso+ deals"
                    _row += apply_markdown_cost(f" 🏆 {i['item_cost_esop_crowns']}")
            elif i['item_cost_gems']:
                _row += apply_markdown_cost(f" {i['item_cost_gems']} or {i['item_cost_seals']}")
            else:
                _row += apply_markdown_cost(f" {i['item_cost_crowns']}")

            # Time left
            if i['item_time_left']:
                _row += apply_markdown_exp(f" ({i['item_time_left']})")
            _list += [_row]

        list_str = '\n'.join(_list)

    # Build final markup
        markdown = f"""
{list_str}
"""
        return markdown

def move_from_featured_to_esop(featured: ScrapedCategory, esop_deals: ScrapedCategory):
    items_to_remove = []

    for i in featured.list:
        if i['item_cost_esop_crowns']:
            esop_deals.list.append(i)
            items_to_remove.append(i)

    for item in items_to_remove:
        featured.list.remove(item)

    esop_deals.remove_duplicates()
    esop_deals.sort_list()
    return featured, esop_deals


### MAIN
if __name__ == '__main__':

    # Special offers
    special_offers = ScrapedCategory('special_offers')

    # Featured
    featured = ScrapedCategory('featured')

    # ESO+ deals
    esop_deals = ScrapedCategory('esop_deals')

    # Move eso+ deals from featured category
    featured, esop_deals = move_from_featured_to_esop(featured, esop_deals)

    # Best deals
    best_deals = ScrapedCategory('best_deals')