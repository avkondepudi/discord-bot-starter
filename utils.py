# Utils methods

import discord
import html
import requests
import random

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def getInsult():
  return html.unescape(requests.get("https://evilinsult.com/generate_insult.php?lang=en&type=json").json()["insult"])

def getCompliment():
  return html.unescape(requests.get("https://complimentr.com/api").json()["compliment"])

def getXKCD(*args):

  if "help" in args:
    return "[number] [\"today\"] [\"info\"]\n\n no args - random comic\n number - specific comic\n today - today's comic\n info - additional info"

  if len(args) > 0 and isfloat(args[0]):
    data = requests.get(f"https://xkcd.com/{args[0]}/info.0.json")
  elif "today" in args:
    data = requests.get(f"https://xkcd.com/info.0.json")
  else:
    num = random.randint(1, int(requests.get(f"https://xkcd.com/info.0.json").json()["num"]))
    data = requests.get(f"https://xkcd.com/{num}/info.0.json")

  try: 
    data.raise_for_status()
  except requests.exceptions.HTTPError:
    return "Comic not found."

  data = data.json()

  if "info" in args:
    return getXKCDEmbed(data)
  else:
    return data["img"]

def getXKCDEmbed(data):
  embedVar = discord.Embed(title=data["safe_title"], color=0x0000FF)
  embedVar.set_image(url=data["img"])
  embedVar.set_footer(text=f"{data['num']} @ {data['year']}-{data['month']}-{data['day']}")

  return embedVar

