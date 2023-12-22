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
  # Sending messages longer than 2000 chars
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


async def has_permissions(interaction):
  # Check if the bot has the necessary permissions in the channel
  permission_bool = interaction.channel.permissions_for(
      interaction.guild.me
  ).send_messages  # required authorization to send messages (in chunks)
  if permission_bool is False:
    await interaction.followup.send(
        "🚫 I'm unable to send messages in this realm. Kindly ask the server's admin and ensure that the 'Send Messages' privilege is given to me and to my honored role in this channel ⚔️🏹"
    )  # followup is webhook, so it can be sent
    return permission_bool  # True/False


@bot.event
async def on_ready():
  print(f'{bot.user} bot is ready on {len(bot.guilds)} servers')
  print('------------------------------------------------')
  scheduled_message_routine.start()


@bot.slash_command(name='help', description="Get help on how I may help you")
async def help(interaction: nextcord.Interaction):
  await interaction.response.defer()
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

  # Check Permissions
  permission_bool = await has_permissions(interaction)
  if permission_bool is False:
    return

  # Special offers
  special_offers = ScrapedCategory('special_offers')
  view = ButtonWithLink(label="👑 See all Special offers",
                        url=URL_SPECIAL_OFFERS)
  chunks = chunk_message(special_offers.markdown)
  for count, chunk in enumerate(chunks):
    if count == 0:
      await interaction.followup.send(chunk)  # send first as reply
    else:
      await interaction.channel.send(chunk)
  await interaction.channel.send('', view=view
                                 )  # send final button for 'special_offers'

  # Featured
  featured = ScrapedCategory('featured')

  # ESO+ deals
  esop_deals = ScrapedCategory('esop_deals')
  featured, esop_deals = move_from_featured_to_esop(featured, esop_deals)

  view = ButtonWithLink(label="👑 See all Featured", url=URL_FEATURED)
  chunks = chunk_message(featured.markdown)
  for chunk in chunks:
    await interaction.channel.send(chunk)
  await interaction.channel.send('',
                                 view=view)  # send final button for 'featured'

  view = ButtonWithLink(label="👑 See all ESO+ deals", url=URL_ESOP_DEALS)
  chunks = chunk_message(esop_deals.markdown)
  for chunk in chunks:
    await interaction.channel.send(chunk)
  await interaction.channel.send('',
                                 view=view)  # send final button for 'featured'


@bot.slash_command(
    name='schedule_daily_feeds_here',
    description='Schedule in this chat daily feeds on Crown Store')
async def schedule_daily_feeds_here(interaction: nextcord.Interaction):
  await interaction.response.defer()

  # Check Permissions
  permission_bool = await has_permissions(interaction)
  if permission_bool is False:
    return

  # Save channel to database
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
    await interaction.followup.send(
        '✅ Feeds correctly scheduled in this chat! Stay tuned 🧙‍♂️')
  else:
    await interaction.followup.send(
        '❌ Something went wrong ... maybe you have not admin permissions in this server ☠️'
    )


@tasks.loop(time=datetime.time(hour=7, minute=37, second=0))  #UTC time
async def scheduled_message_routine():
  print('Daily routine starting...')

  # Special offers
  special_offers = ScrapedCategory('special_offers')
  view_so = ButtonWithLink(label="👑 See all Special offers",
                           url=URL_SPECIAL_OFFERS)
  chunks_so = chunk_message(special_offers.markdown)

  # Featured
  featured = ScrapedCategory('featured')
  view_f = ButtonWithLink(label="👑 See all Featured", url=URL_FEATURED)

  # ESO+ deals
  esop_deals = ScrapedCategory('esop_deals')
  view_ep = ButtonWithLink(label="👑 See all ESO+ deals", url=URL_ESOP_DEALS)
  featured, esop_deals = move_from_featured_to_esop(featured, esop_deals)
  chunks_f = chunk_message(featured.markdown)
  chunks_ep = chunk_message(esop_deals.markdown)

  # Routine
  for guild in bot.guilds:
    try:
      if str(guild.id) in db.keys():
        # get guilds info
        guild_infos = db[str(guild.id)]
        channel = bot.get_channel(guild_infos['channel_id'])
  
        # send Special Offers
        for chunk in chunks_so:
          await channel.send(chunk)
        await channel.send('', view=view_so
                           )  # send final button for 'special_offers'
  
        # send Featured
        for chunk in chunks_f:
          await channel.send(chunk)
        await channel.send('', view=view_f)  # send final button for 'featured'
  
        # send ESO+ deals
        for chunk in chunks_ep:
          await channel.send(chunk)
        await channel.send('', view=view_ep)  # send final button for 'featured'
    except:
      print(f'Error in daily routine for {guild.name}')

keep_alive()
bot.run(os.environ['TOKEN'])
