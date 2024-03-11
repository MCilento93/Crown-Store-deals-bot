# Bot invite link: https://discord.com/api/oauth2/authorize?client_id=1180792508247199835&permissions=3072&scope=bot


### IMPORTING
# Standard library imports
import os, datetime, configparser
from typing import List, Optional, Union

# Third-party library imports
import nextcord
from nextcord.ext import commands, tasks
from nextcord.ui.select import string

# Project entities
from database.database import DataBase
from scraper_crown_store import *


### CLASSES
class ButtonWithLink(nextcord.ui.View):
    def __init__(self, label, url):
        super().__init__()
        self.add_item(nextcord.ui.Button(style=nextcord.ButtonStyle.link,label=label,url=url))


### METHODS
async def has_permissions(interaction):
    permission_bool = False
    # Check if the bot has the necessary permissions in the channel
    if type(interaction.channel) == nextcord.PartialMessageable:
        permission_bool = False
    else:
        permission_bool = interaction.channel.permissions_for(interaction.guild.me).send_messages  # required authorization to send messages
    if permission_bool is False:
        await interaction.followup.send("🚫 I'm unable to send messages in this realm. Kindly ask the server's admin and ensure that the 'Send Messages' privilege is given to me and to my honored role in this channel ⚔️🏹")  # followup is webhook, so it can be sent
        return permission_bool  # bool

async def send_message_to_channel(ctx: Union[nextcord.Interaction,nextcord.abc.Messageable],  # interaction or channel
                                  message: Union[str,nextcord.Embed], # message or embed (with markdown)
                                  first_as_followup: bool = False, # if the first message should be sent as a followup
                                  view: Optional[nextcord.ui.View] = None) -> None:  # optional GUI element
    
    # Chunking auxiliary function (for long messages)
    def chunk_message(string: str,max_chars:int = 2000) -> List[str]:
        # Useful method to send multiple messages in a row
        offset = 0  # 2000 is the character limit in discord, for embeds it is 4096
        chunks = []
        while offset < len(string):
            chunk = string[offset:offset + max_chars]
            reversed_chunk = chunk[::-1]
            length = reversed_chunk.find("\n")
            chunk = chunk[:max_chars - length]
            offset += max_chars - length
            chunks += [chunk]
        return chunks
    
    # Check input message or embeds
    if isinstance(message,str):
        chunks_str = chunk_message(message)  # split code every 2000 chars
        chunks_embed = [None] * len(chunks_str)
    elif isinstance(message,nextcord.Embed):
        chunks_description = chunk_message(message.description,max_chars=4096)  # split code every 4096 chars
        chunks_embed = []
        for chunk in chunks_description:
            chunk_embed = message
            chunk_embed.description = chunk
            chunks_embed += [chunk_embed]
        chunks_str = [None] * len(chunks_embed)
        
    # Check context
    if isinstance(ctx, nextcord.Interaction):
        interaction = ctx
        channel = ctx.channel
    elif isinstance(ctx,nextcord.abc.Messageable):
        interaction = None
        channel = ctx
        first_as_followup=False
    
    # Send message
        # single message to be sent
    if len(chunks_str)==1: 
        if first_as_followup and interaction and view:
            await interaction.followup.send(chunks_str[0],embed=chunks_embed[0],view=view)
        elif first_as_followup and interaction:
            await interaction.followup.send(chunks_str[0],embed=chunks_embed[0])
        elif view:
            await channel.send(chunks_str[0],embed=chunks_embed[0],view=view)
        else: 
            await channel.send(chunks_str[0],embed=chunks_embed[0])
    else:
        # multiple chunks to be sent 
        for count, chunk_str in enumerate(chunks_str):
            chunk_embed = chunks_embed[count]
            if (count == 0 and first_as_followup and interaction is not None):
                # first message to be sent as reply
                await interaction.followup.send(chunk_str,embed=chunk_embed)
            elif count == len(chunks_str)-1:
                # last message with optional view
                if view:
                    await channel.send(chunk_str,embed=chunk_embed,view=view)
                else:
                    await channel.send(chunk_str,embed=chunk_embed)
            else:
                # middle messages
                await channel.send(chunk_str,embed=chunk_embed)
                

### CLIENT METHODS
bot = commands.Bot()

@bot.event
async def on_ready():
    print(f'{bot.user} bot is ready on {len(bot.guilds)} servers')
    print('------------------------------------------------')
    scheduled_message_routine.start()
    await bot.change_presence(activity=nextcord.Game(name=f"""Elder Scrolls in {len(bot.guilds)} discord chat(s)"""))

@bot.slash_command(name='help', description="Get help on how I may help you")
async def help(interaction: nextcord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send(f"""
👋 Greetings adventurers! I'm *{bot.user}* bot, your go-to assistant for Crown Store deals in The Elder Scrolls Online! 🧙‍♂️👑🗡️

**About Me:**
I am unofficial Bethesda bot dedicated to keeping you updated on Crown Store deals in The Elder Scrolls Online.

**How I Help:**
**</crown_store_discounts:1192052807902187580>:** Use me to get the latest offers straight from the Crown Store
**</best_deals:1192052806174134383>:** With this function you will get only my favourite selection of deals
**</schedule_daily_feeds_here:1192052809206607873>:** Admins can set daily deal updates in the chat in which this slash command is invoked

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
    view_s = ButtonWithLink(label="👑 See all Special offers",url=URL_SPECIAL_OFFERS)
    await send_message_to_channel(interaction, special_offers.markdown, first_as_followup=True, view=view_s)

    # Featured
    featured = ScrapedCategory('featured')
    view_f = ButtonWithLink(label="👑 See all Featured", url=URL_FEATURED)
    
    # ESO+ deals
    esop_deals = ScrapedCategory('esop_deals')
    view_e = ButtonWithLink(label="👑 See all ESO+ deals", url=URL_ESOP_DEALS)
    featured, esop_deals = move_from_featured_to_esop(featured, esop_deals)
    await send_message_to_channel(interaction, featured.markdown, view=view_f)
    await send_message_to_channel(interaction, esop_deals.markdown, view=view_e)

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
            'author_id': interaction.user.id,
            'author': interaction.user.name,
        }
        db = DataBase()
        db.upsert(guild_infos)
        db.close_connection()
        await interaction.followup.send('✅ Feeds correctly scheduled in this chat! Stay tuned 🧙‍♂️')
    else:
        await interaction.followup.send('❌ Something went wrong ... maybe you have not admin permissions in this server ☠️')

@tasks.loop(time=datetime.time(hour=3, minute=0, second=0))  #UTC time hosted 24/24
async def scheduled_message_routine():
    print('\nDaily routine starting...')

    # Update presence
    await bot.change_presence(activity=nextcord.Game(name=f"""Elder Scrolls in {len(bot.guilds)} discord chat(s)"""))
    
    # Best deals
    best_deals = ScrapedCategory('best_deals')
    embed = nextcord.Embed(title=best_deals.title, description=best_deals.markdown_no_title,color=nextcord.Colour.lighter_grey())
    embed.set_thumbnail('https://raw.githubusercontent.com/MCilento93/Crown-Store-deals-bot/main/icons/icon_alpha.png')
    embed.set_footer(text='Crown Store deals | Best deals')

    # Routine
    for guild in bot.guilds:
        try:
            db = DataBase()
            channel_id = db.get_channel_id(guild.id)
            db.close_connection()
            if channel_id:
                channel = bot.get_channel(channel_id)
                await send_message_to_channel(channel,embed)  
        except:
            print(f'Error in daily routine for {guild.name}')


### MAIN
config = configparser.ConfigParser()
config.read('config.ini')
bot.run(config['BOT_SETTINGS']['TOKEN'])