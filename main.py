#bot invite link: https://discord.com/api/oauth2/authorize?client_id=1180792508247199835&permissions=3072&scope=bot

### IMPORTING
import os, datetime  #, asyncio
import nextcord
from nextcord.ext import tasks, commands
from nextcord.ui.select import string
from keep_alive import keep_alive
from scraper_crown_store import *
from replitapi import db


### GUI
class ButtonWithLink(nextcord.ui.View):

  def __init__(self, label, url):
    super().__init__()
    self.add_item(
        nextcord.ui.Button(style=nextcord.ButtonStyle.link,
                           label=label,
                           url=url))


### FUNCTIONS
bot = commands.Bot()


def chunk_message(message: str):
  offset = 0  # 2000 is the character limit in discord
  chunks = []
  while offset < len(message):
    chunk = message[offset:offset + 2000]
    reversed_chunk = chunk[::-1]
    length = reversed_chunk.find("\n")
    chunk = chunk[:2000 - length]
    offset += 2000 - length
    chunks += [chunk]
  return chunks


@bot.event
async def on_ready():
  print(f'{bot.user} bot is ready on {len(bot.guilds)} servers')
  print('------------------------------------------------')
  scheduled_message_routine.start()


@bot.slash_command(name='help', description="Get help on how I may help you")
async def help(interaction: nextcord.Interaction):
  await interaction.response.defer()
  # await asyncio.sleep(1)
  await interaction.followup.send(f"""
👋 Greetings adventurers! I'm *{bot.user}* bot, your go-to assistant for Crown Store deals in The Elder Scrolls Online! 🧙‍♂️👑🗡️

**About Me:**
I am unofficial Bethesda bot dedicated to keeping you updated on Crown Store deals in The Elder Scrolls Online.

**How I Help:**
- **/crown_store_discounts:** Use me to get the latest offers straight from the Crown Store.
- **/schedule_daily_deals_here:** Admins can set daily deal updates in the chat in which the slash command is invoked

Stay ahead with the best deals in the Crown Store. Happy gaming! ⚔️👑🏹
""")


@bot.slash_command(name='crown_store_discounts',
                   description='Sending latest crown store deals')
async def crown_store_discounts(interaction: nextcord.Interaction):
  await interaction.response.defer()

  # Special offers
  # html = await get_html(URL_SPECIAL_OFFERS)
  html = get_html(URL_SPECIAL_OFFERS)
  special_offers = scrape_special_offers(html)
  view = ButtonWithLink(label="👑 See all Special offers",
                        url=URL_SPECIAL_OFFERS)
  # await asyncio.sleep(1)
  await interaction.followup.send(special_offers[0], view=view)

  # Featured
  # html = await get_html(URL_FEATURED)
  html = get_html(URL_FEATURED)
  featured = scrape_featured(html)
  view = ButtonWithLink(label="👑 See all Featured", url=URL_FEATURED)
  # await asyncio.sleep(1)
  chunks = chunk_message(featured[0])
  for chunk in chunks:
    await interaction.channel.send(chunk)
  await interaction.channel.send('',
                                 view=view)  # send final button for 'featured'


@bot.slash_command(
    name='schedule_daily_feeds_here',
    description='Schedule in this chat daily feeds on Crown Store')
async def schedule_daily_feeds_here(interaction: nextcord.Interaction):
  await interaction.response.defer()
  if interaction.user.id == interaction.guild.owner_id:
    guild_infos = {
        'guild_id': interaction.guild_id,
        'guild_name': interaction.guild.name,
        'channel_id': interaction.channel_id,
        'channel_name': interaction.channel.name,
        'author': interaction.user.name,
        'author_id': interaction.user.id
    }
    db[str(guild_infos['guild_id'])] = guild_infos
    # await asyncio.sleep(1)
    await interaction.followup.send(
        '✅ Feeds correctly scheduled in this chat! Stay tuned 🧙‍♂️')
  else:
    # await asyncio.sleep(1)
    await interaction.followup.send(
        '❌ Something went wrong ... maybe you have not admin permissions in this server ☠️'
    )


@tasks.loop(time=datetime.time(hour=3, minute=10, second=0))  #UTC time
async def scheduled_message_routine():
  print('Daily routine starting...')

  # Special offers
  html_so = get_html(URL_SPECIAL_OFFERS)
  special_offers = scrape_special_offers(html_so)
  view_so = ButtonWithLink(label="👑 See all Special offers",
                           url=URL_SPECIAL_OFFERS)

  # Featured
  html_f = get_html(URL_FEATURED)
  featured = scrape_featured(html_f)
  view_f = ButtonWithLink(label="👑 See all Featured", url=URL_FEATURED)
  # await asyncio.sleep(1)
  chunks = chunk_message(featured[0])

  # Routine
  for guild in bot.guilds:
    if str(guild.id) in db.keys():
      # get guilds info
      guild_infos = db[str(guild.id)]
      channel = bot.get_channel(guild_infos['channel_id'])

      # send Special Offers
      await channel.send(str(special_offers[0]), view=view_so)

      # send Featured
      for chunk in chunks:
        await channel.send(chunk)
      await channel.send('', view=view_f)  # send final button for 'featured'


keep_alive()
bot.run(os.environ['TOKEN'])
