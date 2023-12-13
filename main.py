import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import os
import requests
import shutil
from math import floor, ceil
from typing import Tuple, Optional
import random, asyncio
from discord import app_commands

# Bot 
INTENTS = discord.Intents.all()
INTENTS.members = True
bot = commands.Bot(command_prefix='?', intents=INTENTS)

# Constants
XP_PER_LVL = 500  
FOREST_CHOP_TIMER = 3 # seconds
MINE_TIMER = 5 

# Player stats
players = {}

# Inventory system
inventories = {} 

# Currency  
wallet = {}

# Environment 
forest = {}
mines = {}

# Items  
tools = ['Rusty Axe', 'Rusty Pickaxe', 'Fishing Rod', 'Hoe', 'Sword']
crops = ['Parsnip', 'Green Bean', 'Potato']
goods = ['Wood', 'Stone', 'Coal', 'Iron Ore', 'Copper Ore']

# XP system
lvl_data = {}

# Profile embed
async def create_profile_embed(player):
    player_data = players[player.id]
    
    embed = discord.Embed(title=f"{player.display_name}'s Profile")
    embed.add_field(name="Level", value=player_data['lvl'])
    embed.add_field(name="XP", value=f"{player_data['xp']}/{XP_PER_LVL*(player_data['lvl']+1)}")
    embed.add_field(name="Wallet", value=f"${wallet.get(player.id, 0)}")
    
    return embed

@bot.command()
async def profile(ctx):  
    embed = await create_profile_embed(ctx.author)
    await ctx.send(embed=embed)
    
@bot.command()
async def chop(ctx):
    player = ctx.author
    
    if 'Rusty Axe' not in inventories.get(player.id, {}):
        return await ctx.send("You don't have a rusty axe!")
        
    await gather_wood(ctx, player)
    
async def gather_wood(ctx, player):
    await ctx.send(f"{player.display_name} started chopping wood...")
    await asyncio.sleep(FOREST_CHOP_TIMER) 
    
    wood_amnt = random.randint(5, 20)
    inventories.setdefault(player.id, {}).setdefault('Wood', 0)
    inventories[player.id]['Wood'] += wood_amnt
    
    await ctx.send(f"{player.display_name} gathered {wood_amnt} Wood!")

@bot.command()
async def mine(ctx):
    player = ctx.author
    
    if 'Rusty Pickaxe' not in inventories.get(player.id, {}):
        return await ctx.send("You don't have a rusty pickaxe!")
        
    await mine_ores(ctx, player)

async def mine_ores(ctx, player):
    await ctx.send(f"{player.display_name} started mining...")
    await asyncio.sleep(MINE_TIMER) 
    
    ore_amnt = random.randint(1, 5)
    ore_type = random.choice(['Coal', 'Iron Ore', 'Copper Ore'])
    inventories.setdefault(player.id, {}).setdefault(ore_type, 0)
    inventories[player.id][ore_type] += ore_amnt
    
    await ctx.send(f"{player.display_name} mined {ore_amnt} {ore_type}!")

@bot.command()
async def plant(ctx, crop):
    player = ctx.author
    
    if crop not in crops:
        return await ctx.send("Invalid crop! Choose from: " + ', '.join(crops))
    
    if 'Hoe' not in inventories.get(player.id, {}):
        return await ctx.send("You don't have a hoe to plant the crop!")
        
    await plant_crop(ctx, player, crop)

async def plant_crop(ctx, player, crop):
    await ctx.send(f"{player.display_name} planted a {crop}...")
    await asyncio.sleep(5)  # Adjust the time it takes for the crop to grow
    
    crop_amnt = random.randint(1, 3)
    inventories.setdefault(player.id, {}).setdefault(crop, 0)
    inventories[player.id][crop] += crop_amnt
    
    await ctx.send(f"{player.display_name}'s {crop} grew! You harvested {crop_amnt} {crop}!")

@bot.command()
async def sell(ctx, item, amount=1):
    player = ctx.author
    
    if item not in goods:
        return await ctx.send("Invalid item! Choose from: " + ', '.join(goods))
    
    if item not in inventories.get(player.id, {}):
        return await ctx.send(f"You don't have any {item} to sell!")
    
    sell_price = random.randint(5, 15)
    total_price = sell_price * amount
    
    inventories[player.id][item] -= amount
    wallet.setdefault(player.id, 0)
    wallet[player.id] += total_price
    
    await ctx.send(f"{player.display_name} sold {amount} {item}(s) for ${total_price}!")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event  
async def on_message(message):
    await add_xp(message.author, random.randint(15, 25)) 

async def add_xp(player, xp):
    lvl_data.setdefault(player.id, {'xp': 0, 'lvl': 1})
    lvl_data[player.id]['xp'] += xp
    lvl_data[player.id]['lvl'] = int(lvl_data[player.id]['xp'] / XP_PER_LVL)

@bot.command()
async def rank(ctx, member: Optional[discord.Member] = None):
    member = member or ctx.author
    xp = xp_data.get(member.id, 0)  # Replace with your method to get XP
    
    username = member.display_name
    image_path = await render_lvl_image(member, username, xp)
    
    if image_path:
        with open(image_path, "rb") as file:
            await ctx.send(file=discord.File(file, "rank.png"))
    else:
        await ctx.send("Failed to generate the rank image.")

# Rendering functions
def get_xp(xp: int, monthly_xp: int) -> str:
    return f"{xp} XP all-time, {monthly_xp} XP this month"

def download_avatar(url: str, filename: str) -> bool:
    try:
        response = requests.get(url, stream=True)
        with open(filename, 'wb') as outfile:
            shutil.copyfileobj(response.raw, outfile)
        del response
        return True
    except requests.exceptions.ConnectionError as err:
        print(f"Issue downloading avatar {url}. Aborting")
        print(str(err))
        return False

async def render_lvl_image(user: discord.Member, username: str, xp: int) -> Optional[str]:
    if not os.path.exists(TMP_PATH):
        os.makedirs(TMP_PATH)

    lvl = floor(xp / XP_PER_LVL)
    bar_num = ceil(10 * (xp - (lvl * XP_PER_LVL)) / XP_PER_LVL)
    rank = xp_data.get(user.id, 0)  # Replace with your method to get rank

    out_filename = os.path.join(TMP_PATH, f"{user.id}.png")
    avatar_filename = out_filename

    avatar_url = user.display_avatar.url

    success = await download_avatar(avatar_url, avatar_filename)
    if not success:
        return None

    bg = Image.open(IMG_BG)
    avatar = Image.open(avatar_filename).convert("RGBA")
    frame = Image.open(IMG_FRAME)
    small_bar = Image.open(IMG_SM_BAR)
    large_bar = Image.open(IMG_LG_BAR)

    avatar = avatar.resize((68, 68))
    bg.paste(avatar, (16, 14), avatar)
    bg.paste(frame, (14, 12), frame)

    for i in range(0, bar_num):
        if i % 5 == 4:
            bg.paste(large_bar, (BAR_X[i], BAR_Y), large_bar)
        else:
            bg.paste(small_bar, (BAR_X[i], BAR_Y), small_bar)

    draw = ImageDraw.Draw(bg)
    font_14 = ImageFont.load_default()
    font_22 = ImageFont.load_default()
    
    draw.text(USERNAME_POS.shadow_tuple(), username, BACK_COLOR, font=font_22)
    draw.text(USERNAME_POS.as_tuple(), username, FONT_COLOR, font=font_22)

    draw.text(LEVEL_POS.shadow_tuple(), f"Level {lvl}", BACK_COLOR, font=font_22)
    draw.text(LEVEL_POS.as_tuple(), f"Level {lvl}", FONT_COLOR, font=font_22)

    rank_text = f"Server Rank : {rank}"
    rank_width = font_14.getlength(rank_text)
    draw.text((RANK_POS.x - rank_width, RANK_POS.y), rank_text, BACK_COLOR, font=font_14)

    bg.save(out_filename)
    bg.close()
    avatar.close()
    frame.close()
    small_bar.close()
    large_bar.close()

    return out_filename

@bot.tree.command()
async def modupload(
    interaction: discord.Interaction,
    zip_file: discord.Attachment,
    description: str,
    images: list
):
    await interaction.channel.send(f"Mod upload received!\nDescription: {description}\nImages: {len(images)} images") 
    await interaction.user.send(files=[zip_file] + images)

@bot.tree.command(name="contest_start", description="Start a contest")
@app_commands.checks.has_role("Admin")  
async def contest_start(interaction: discord.Interaction):
    channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
    await channel.send("Contest has started! Here is the schedule:")
    
    for i in range(3):
        event = random.choice(["Fishing Contest", "Luau", "Dance of the Moonlight Jellies"])
        date = random.randint(1, 28)
        await channel.send(f"{event} on the {date}")
        
@bot.tree.command(name="stardewwiki")
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
    
import os
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
