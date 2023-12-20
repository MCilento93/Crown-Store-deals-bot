# python -i permissions/permissions_check.py

import os
import nextcord
from nextcord.ext import tasks, commands
from replitapi import db

bot = commands.Bot()


@bot.event
async def on_ready():
  print(f'{bot.user} bot is ready on {len(bot.guilds)} servers')
  print('Permission check routine')
  print('------------------------------------------------')
  
  for guild in bot.guilds:
    if str(guild.id) in db.keys():
      guild_infos = db[str(guild.id)]
      channel = bot.get_channel(guild_infos['channel_id'])
      permissions=channel.permissions_for(guild.me)
      print(f"Permissions in {guild.name} @channel {channel.name}:")
      print(dict(permissions))

bot.run(os.environ['TOKEN'])

# Permissions in test server di giolarochelle @channel generale:
# {'create_instant_invite': True, 
#  'kick_members': False, 
#  'ban_members': False, 
#  'administrator': False, 
#  'manage_channels': False, 
#  'manage_guild': False, 
#  'add_reactions': True, 
#  'view_audit_log': False, 
#  'priority_speaker': False, 
#  'stream': False, 
#  'read_messages': True, 
#  'send_messages': True, 
#  'send_tts_messages': False, 
#  'manage_messages': False, 
#  'embed_links': True, 
#  'attach_files': True, 
#  'read_message_history': True, 
#  'mention_everyone': True, 
#  'external_emojis': True, 
#  'view_guild_insights': False, 
#  'connect': False, 
#  'speak': False, 
#  'mute_members': False, 
#  'deafen_members': False, 
#  'move_members': False, 
#  'use_voice_activation': False, 
#  'change_nickname': True, 
#  'manage_nicknames': False, 
#  'manage_roles': False, 
#  'manage_webhooks': False, 
#  'manage_emojis': False, 
#  'use_slash_commands': True, 
#  'request_to_speak': True, 
#  'manage_events': False, 
#  'manage_threads': False, 
#  'create_public_threads': True, 
#  'create_private_threads': True, 
#  'external_stickers': True, 
#  'send_messages_in_threads': True, 
#  'start_embedded_activities': True, 
#  'moderate_members': False}