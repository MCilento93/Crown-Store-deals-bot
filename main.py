# Bot invite link: https://discord.com/api/oauth2/authorize?client_id=1180792508247199835&permissions=3072&scope=bot


### IMPORTING
# Standard library imports
import datetime
import os
from typing import List, Optional, Union

# Third-party library imports
import nextcord
from nextcord.ext import commands, tasks
from nextcord.ui.select import string
from replitapi import db

# Project entities
from keep_alive import keep_alive
from scraper_crown_store import *


### CLIENT
bot = commands.Bot()


### CLASSES
class ButtonWithLink(nextcord.ui.View):
    def __init__(self, label, url):
        super().__init__()
        self.add_item(nextcord.ui.Button(style=nextcord.ButtonStyle.link,label=label,url=url))


### FUNCTIONS
def chunk_message(message: str,max_chars:int = 2000) -> List[str]:
    # Sending messages longer than 2000 chars
    offset = 0  # 2000 is the character limit in discord, for embed it is 4096
    chunks = []
    while offset < len(message):
        chunk = message[offset:offset + max_chars]
        reversed_chunk = chunk[::-1]
        length = reversed_chunk.find("\n")
        chunk = chunk[:max_chars - length]
        offset += max_chars - length
        chunks += [chunk]
    return chunks

async def has_permissions(interaction):
    # Check if the bot has the necessary permissions in the channel
    if type(interaction.channel) == nextcord.PartialMessageable:
        permission_bool = False
    else:
        permission_bool = interaction.channel.permissions_for(interaction.guild.me).send_messages  # required authorization to send messages (in chunks)

    if permission_bool is False:
        await interaction.followup.send(
            "🚫 I'm unable to send messages in this realm. Kindly ask the server's admin and ensure that the 'Send Messages' privilege is given to me and to my honored role in this channel ⚔️🏹")  # followup is webhook, so it can be sent
        return permission_bool  # True/False

async def send_message_to_channel(ctx: Union[nextcord.Interaction,nextcord.abc.Messageable],  # interaction or channel as input
                                  markdown: Optional[str] = None,
                                  embed: Optional[nextcord.Embed] = None,
                                  first_as_followup: bool = False,
                                  view: Optional[nextcord.ui.View] = None) -> None:  # optional GUI element here

    if markdown:
        chunks = chunk_message(markdown)  # split code every 2000 chars
    elif embed:
        chunks = chunk_message(embed.description,max_chars=4096)  # split code every 4096 chars
    
    # If an interaction is sent
    if isinstance(ctx, nextcord.Interaction):
        interaction = ctx
        channel = ctx.channel
    # If a channel is sent
    else:
        interaction = None
        channel = ctx
    
    # Send message
    for count, chunk in enumerate(chunks):
        if (count == 0 and first_as_followup and interaction is not None):
            await interaction.followup.send(chunk)  # send first as reply
        else:
            if embed:
                _embed = embed
                _embed.description = chunk
                await channel.send(embed=_embed)
            else: 
                await channel.send(chunk)
    if view:
        await channel.send('', view=view)  # send a final message with button

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
- **/crown_store_discounts:** Use me to get the latest offers straight from the Crown Store
- **/best_deals:** With this function you will get only my favourite selection of deals
- **/schedule_daily_deals_here:** Admins can set daily deal updates in the chat in which this slash command is invoked

Stay ahead with the best deals in the Crown Store. Happy gaming! ⚔️👑🏹
""")

@bot.slash_command(name='crown_store_discounts',description='Sending latest crown store deals')
async def crown_store_discounts(interaction: nextcord.Interaction):
    await interaction.response.defer()

    # Check Permissions
    permission_bool = await has_permissions(interaction)
    if permission_bool is False:
        return

    # Special offers
    special_offers = ScrapedCategory('special_offers')
    view = ButtonWithLink(label="👑 See all Special offers",url=URL_SPECIAL_OFFERS)
    await send_message_to_channel(interaction,
                                  special_offers.markdown,
                                  first_as_followup=True,
                                  view=view)

    # Featured
    featured = ScrapedCategory('featured')

    # ESO+ deals
    esop_deals = ScrapedCategory('esop_deals')
    featured, esop_deals = move_from_featured_to_esop(featured, esop_deals)

    view = ButtonWithLink(label="👑 See all Featured", url=URL_FEATURED)
    await send_message_to_channel(interaction, featured.markdown, view=view)

    view = ButtonWithLink(label="👑 See all ESO+ deals", url=URL_ESOP_DEALS)
    await send_message_to_channel(interaction, esop_deals.markdown, view=view)

@bot.slash_command(name='best_deals',description='Sending only my selection of crown store deals')
async def best_deals(interaction: nextcord.Interaction):
    await interaction.response.defer()

    # Check Permissions
    permission_bool = await has_permissions(interaction)
    if permission_bool is False:
        return

    # Best deals
    best_deals = ScrapedCategory('best_deals')
    await send_message_to_channel(interaction,
                                  best_deals.markdown,
                                  first_as_followup=True)

@bot.slash_command(name='schedule_daily_feeds_here',description='Schedule in this chat daily feeds on Crown Store')
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
        await interaction.followup.send('✅ Feeds correctly scheduled in this chat! Stay tuned 🧙‍♂️')
    else:
        await interaction.followup.send('❌ Something went wrong ... maybe you have not admin permissions in this server ☠️')

@tasks.loop(time=datetime.time(hour=3, minute=10, second=0))  #UTC time
async def scheduled_message_routine():
    print('Daily routine starting...')

    # Best deals
    best_deals = ScrapedCategory('best_deals')
    embed = nextcord.Embed(title=best_deals.title, description=best_deals.markdown_no_title,color=nextcord.Colour.lighter_grey())
    
    # Routine
    for guild in bot.guilds:
        try:
            if str(guild.id) in db.keys():
                # get guilds info
                guild_infos = db[str(guild.id)]
                channel = bot.get_channel(guild_infos['channel_id'])
                await send_message_to_channel(channel,embed)   
        except:
            print(f'Error in daily routine for {guild.name}')


### MAIN
keep_alive()
bot.run(os.environ['TOKEN'])