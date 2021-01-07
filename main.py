# Discord Bot Starter

from datetime import datetime, timedelta, timezone
from dateutil import tz

import os
import sys

import discord
from discord.ext import commands

import asyncio
import pickle

from utils import getInsult, getCompliment, getXKCD

# global vars
TIME_ZONE = "America/New_York"
ADMIN_FILE = "admin.pkl"
ADMIN_FILE_MAX_MESSAGES = 1000
MUTED = []

# for Admin feature
intents = discord.Intents.all()

COMMAND_PREFIX = "!"
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

def addToAdminFile(message):
  global ADMIN_FILE, ADMIN_FILE_MAX_MESSAGES

  if os.path.exists(ADMIN_FILE):
    with open(ADMIN_FILE, "rb") as fp:
      original = pickle.load(fp)
  else:
    original = []

  if len(original) < ADMIN_FILE_MAX_MESSAGES: 
    original.append(message)
  else: 
    original = original[1:]
    original.append(message)

  with open(ADMIN_FILE, "wb") as fp:
    pickle.dump(original, fp)

@bot.event
async def on_ready():

  print("Logged in as")
  print(bot.user.name)
  print(bot.user.id)
  print(datetime.now().strftime("%H:%M:%S"))
  print("------")

@bot.event
async def on_message(message):
  global MUTED

  if message.author.id in MUTED:
    await message.delete()

  await bot.process_commands(message)

@bot.event
async def on_member_join(member):
  addToAdminFile(f"{member} joined")

@bot.event
async def on_member_remove(member):
  addToAdminFile(f"{member} left")
  
@bot.event
async def on_member_update(before, after):
  global TIME_ZONE
  
  time = datetime.utcnow().replace(tzinfo=tz.tzutc()).astimezone(tz.gettz(TIME_ZONE)).strftime("%m-%d %H:%M:%S")
  if str(before.status) != str(after.status):

    message = f"[{time}] {after.name} went from {str(before.status)} to {str(after.status)}"
    addToAdminFile(message)

'''
on_reaction_add and on_reaction_remove enabled for Starboard feature

To use, must:
* enable privileged gateway intents in discord developer portal
* create text channel named "starboard"
'''

@bot.event
async def on_reaction_add(reaction, user):

  message = reaction.message
  emoji = reaction.emoji

  if message.author.id != bot.user.id and emoji == "⭐":

    channel_id = -1
    for guild in bot.guilds:
      if guild.id == user.guild.id:
        for channel in guild.text_channels:
          if channel.name == "starboard":
            channel_id = channel.id
            break

      if channel_id != -1:
        break

    if channel_id == -1:
      return

    channel = bot.get_channel(channel_id)

    messages = await channel.history(limit=50).flatten()
    for starred_msg in messages:
      if (len(starred_msg.embeds) > 0 and 
          starred_msg.embeds[0].footer.text != discord.Embed.Empty and
          int(starred_msg.embeds[0].footer.text.split()[1])) == message.id:

        num = int(starred_msg.content.split()[1].strip("*"))
        num += 1
        new_content = starred_msg.content.split()[0] + f" **{num}** " + " ".join(starred_msg.content.split()[2:])
        await starred_msg.edit(content=new_content, embed=starred_msg.embeds[0])

        return

    embedVar = discord.Embed(description=f"{message.content}\n\n[**Click to jump to message!**](https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id})")
    embedVar.set_author(name=str(message.author), icon_url=message.author.avatar_url)
    embedVar.set_footer(text=f"MessageID: {message.id} • {message.created_at.strftime('%m/%d/%Y')}")

    if len(message.attachments) > 0:
      embedVar.set_image(url=message.attachments[0].url)

    num = 1
    starred_msg = await channel.send(f"⭐ **{num}** | <#{message.channel.id}>", embed=embedVar)
    await starred_msg.add_reaction(emoji="⭐")

@bot.event
async def on_raw_reaction_remove(event):

  emoji = event.emoji.name

  if event.user_id != bot.user.id and emoji == "⭐":

    channel_id = -1
    for guild in bot.guilds:
      if guild.id == event.guild_id:
        for channel in guild.text_channels:
          if channel.name == "starboard":
            channel_id = channel.id
            break

      if channel_id != -1:
        break

    if channel_id == -1:
      return

    channel = bot.get_channel(channel_id)

    messages = await channel.history(limit=50).flatten()
    for starred_msg in messages:
      if len(starred_msg.embeds) > 0 and int(starred_msg.embeds[0].footer.text.split()[1]) == event.message_id:

        num = int(starred_msg.content.split()[1].strip("*"))

        if num == 1:
          await starred_msg.delete()
        else:
          num -= 1
          new_content = starred_msg.content.split()[0] + f" **{num}** " + " ".join(starred_msg.content.split()[2:])
          await starred_msg.edit(content=new_content, embed=starred_msg.embeds[0])

@bot.command()
async def ping(ctx):
  await ctx.send("pong")

@bot.command(pass_context=True)
async def restart(ctx):
  await ctx.send("Restarting...")
  os.execv(sys.executable, ['python3'] + sys.argv)

@bot.command(pass_context=True)
async def mute(ctx, user: discord.Member = None):
  global MUTED

  MUTED.append(user.id)
  await ctx.send(f"muted {user.name}")

@bot.command(pass_context=True)
async def unmute(ctx, user: discord.Member = None):
  global MUTED

  MUTED = [i for i in MUTED if i != user.id]
  await ctx.send(f"unmuted {user.name}")

@bot.command(pass_context=True)
async def mention(ctx, user: discord.Member = None):
  if user is None:
    await ctx.send("User not found")
  else:
    await user.send(f"{ctx.message.author.name} mentioned you in {ctx.message.channel.name}!")
    await ctx.send(f"Mention sent to {user.name}")

@bot.command()
async def woo(ctx):
  await ctx.send("https://tenor.com/view/theoffice-gif-4724042")

@bot.command()
async def insult(ctx, user: discord.Member = None):
  await ctx.send(f"{getInsult()} <@{user.id}>")

@bot.command()
async def compliment(ctx, user: discord.Member = None):
  await ctx.send(f"{getCompliment()} <@{user.id}>")

@bot.command()
async def xkcd(ctx, *args):
  output = getXKCD(*args)
  if isinstance(output, str):
    await ctx.send(output)
  else:
    await ctx.send(embed=output)

@bot.command(pass_context=True)
async def admin(ctx, user: discord.Member = None):
  '''Method to access logs

  Pass user to access logs for that specific user
  '''
  global ADMIN_FILE

  if os.path.exists(ADMIN_FILE):
    with open(ADMIN_FILE, "rb") as fp:
      original = pickle.load(fp)
  else:
    await ctx.send("Admin file not found")
    return

  if user:  
    original = [msg for msg in original if user.name in msg]

  output = "```nim\n"

  original = original[::-1][:20]
  for msg in original[::-1]:
    output += msg+"\n"

  output += "```"
  await ctx.send(output)

# Add your own methods here!

if __name__ == "__main__":
  TOKEN = os.getenv("BOTTOKEN")
  bot.run(TOKEN)
