import discord
from discord.ext import commands
from discord import app_commands
import random

INTENTS = discord.Intents.all()
INTENTS.members = True
bot = commands.Bot(command_prefix='?', intents=INTENTS)

@tree.command(name="modupload", description="Upload a mod")
@app_commands.describe(zip_file="The mod ZIP file", description="A description of the mod", images="Image files of the mod")
async def modupload(interaction: discord.Interaction, zip_file: discord.Attachment, description: str, images: list[discord.Attachment]):
    await interaction.channel.send(f"Mod upload received!\nDescription: {description}\nImages: {len(images)} images")
    await interaction.user.send(files=[zip_file] + images)

@tree.command(name="contest_start", description="Start a contest")
@app_commands.checks.has_role("Admin")
async def contest_start(interaction: discord.Interaction):
    channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
    await channel.send("Contest has started! Here is the schedule:")
    
    for i in range(3):
        event = random.choice(["Fishing Contest", "Luau", "Dance of the Moonlight Jellies"])
        date = random.randint(1, 28)
        await channel.send(f"{event} on the {date}")

import requests
from bs4 import BeautifulSoup

@tree.command(name="stardewwiki")
async def stardewwiki(interaction: discord.Interaction, search: str):
    url = f"https://stardewvalleywiki.com/Search?query={search}"
    
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    first_result = soup.select_one('div.searchdidyoumean')
    
    if not first_result:
        await interaction.response.send_message("No results found")
        return

    title = first_result.select_one('a').text
    image_url = "https:" + first_result.select_one('img')['src']
        
    # Fetch content for result page 
    result_url = "https://stardewvalleywiki.com" + first_result.select_one('a')['href']
    res = requests.get(result_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    content = soup.select_one('div#mw-content-text').getText()[:500] + "..."
    
    embed = discord.Embed(title=title, url=result_url, description=content) 
    embed.set_image(url=image_url)
    embed.set_footer(text="Information from Stardew Valley Wiki")
    
    await interaction.response.send_message(embed=embed)
