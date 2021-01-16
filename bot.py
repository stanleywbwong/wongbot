# Developed by Stan

import os

import discord
import asyncio
import json
import re
from discord.ext import commands
from dotenv import load_dotenv

# Load in environment variables, set up bot user
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN').strip('{}')
GUILD = os.getenv('DISCORD_GUILD').strip('{}')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

# Runs once bot is connected and available.
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    guild = discord.utils.get(bot.guilds, name=GUILD)

    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    # Load currency data from json
    global user_amounts
    try:
        with open('user_amounts.json') as f:
            user_amounts = json.load(f)
            print(f"loaded user amounts: {user_amounts}")
    except FileNotFoundError:
        print("Could not load user_amounts.json")
        user_amounts = {}

############################
###### GENERAL EVENTS ######
############################

@bot.event
async def on_member_join(member):
    guild = discord.utils.get(bot.guilds, name=GUILD)
    general = discord.utils.get(guild.channels, name='general')
    await general.send(f'{member.name} HAS BEEN ASSIMILATED.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content == 'wongbot awaken':
        await message.channel.send(f'WONGBOT ACTIVATED')
    
    if 'casino' in message.content:
        await message.channel.send(f'CASINO UNDER DEVELOPMENT')

    if 'anime' in message.content.lower() or 'manga' in message.content.lower():
        await message.channel.send(f'WEEB DETECTED. BAN COMMENCING IN 10 SECONDS')
        await weeb_ban(message)

    if 'catgirl' in message.content:
        await message.channel.send(f'NO CATGIRLS ALLOWED. BAN COMMENCING IN 10 SECONDS')
        await weeb_ban(message)

    await bot.process_commands(message)

async def weeb_ban(message):
    guild = discord.utils.get(bot.guilds, name=GUILD)
    offender = discord.utils.get(guild.members, name=message.author)
    for i in range(10, -1, -1):
        await message.channel.send(content=str(i), delete_after=1)
        await asyncio.sleep(1)
    await message.channel.send(f"TIME'S UP. GOODBYE WEEB", delete_after=2)

    # ban
    #await guild.ban(message.author, reason='WEEB DETECTED', delete_message_days=0)

    # kick
    await guild.kick(message.author)

    # remove from voice
    #await offender.edit(voice_channel=None)
    
    await message.channel.send(f'{message.author} REMOVED, GOOD WORK TEAM')

############################
###### ERROR HANDLING ######
############################

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('WHERE TF ARE YOUR PERMISSIONS BOYO')
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('INVALID COMMAND DIPSHIT')

@bot.event
async def on_error(event, *args, **kwargs):
    message = args[0] # extract message from args
    if 'anime' in message.content or 'manga' in message.content:
        await message.channel.send('BAN HAMMER BROKEN, TERRORISTS WIN')

############################
##### GENERAL COMMANDS #####
############################

@bot.command(help='check stanleys ping lmao')
async def ping(ctx):
    await ctx.send(f'Pong! Ping: {round(bot.latency * 1000)}ms.')

@bot.command(help='can i get uhhh vibe check')
async def vibecheck(ctx):
    await ctx.send(f'CHECKING VIBE...')
    await asyncio.sleep(3)
    await ctx.send(f'VIBE CHECKED')

############################
##### ECONOMY COMMANDS #####
############################

@bot.command(help='displays stanbucks balance')
async def balance(ctx):
    global user_amounts
    request_id = str(ctx.message.author.id)
    print(f"balance requested by {request_id}")
    print(f"available user_amounts: {user_amounts}")
    if request_id in user_amounts:
        await ctx.send("BALANCE: {} STANBUCKS".format(user_amounts[request_id]['balance']))
    else:
        await ctx.send(f"NO ACCOUNT. REGISTER WITH '$register'")

@bot.command(help='opt in to the stanbucks economy')
async def register(ctx):
    global user_amounts
    request_id = str(ctx.message.author.id)
    if request_id not in user_amounts:
        account = {'balance': 10000}
        user_amounts[request_id] = account
        await ctx.send("REGISTRATION SUCCESSFUL")
        print(user_amounts)
        _save() 
    else:
        await ctx.send("YOU ALREADY HAVE AN ACCOUNT NICE TRY IDIOT")

@bot.command()
async def transfer(ctx, amount: int, other: discord.Member):
    global user_amounts
    primary_id = str(ctx.message.author.id)
    other_id = str(other.id)
    if primary_id not in user_amounts:
        await ctx.send("NO ACCOUNT. REGISTER WITH '$REGISTER'")
    elif other_id not in amounts:
        await ctx.send("OTHER PARTY DOES NOT HAVE AN ACCOUNT.")
    elif user_amounts[primary_id]['balance'] < amount:
        await ctx.send("NO OVERDRAFTING GTFO")
    else:
        user_amounts[primary_id]['balance'] -= amount
        user_amounts[other_id]['balance'] += amount
        await ctx.send("TRANSACTION COMPLETED")
    _save()

def _save():
    global user_amounts
    print("user amounts to be saved: ", user_amounts)
    with open('user_amounts.json', 'w+') as f:
        json.dump(user_amounts, f)

@bot.command(name='bet', help='gamble stanbucks against ur friends')
async def bet(ctx, *, question):
    await ctx.send(f"Question: {question}")
    await ctx.send(f"Provide two options to bet on (split with OR):")

    # checks that option provider is bet creator
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel
    
    # prompt for options
    try:
        options_string = await bot.wait_for('message', check=check, timeout=10)
    except asyncio.TimeoutError:
        await ctx.send("Timed out. Try again.")
        return

    options = options_string.content.split('OR')
    option1, option2 = options[0].strip(), options[1].strip()
    await ctx.send(f"Option 1: {option1} \nOption 2: {option2}")
    await ctx.send(f"TIME TO PLACE YOUR BETS")

    def bet_check(msg):
        print('got to bet check')
        valid_bet = re.compile(r"bet \d+")
        print(f'valid_bet: {valid_bet}')
        return valid_bet.match(msg.content) != None

    pot = 0
    placed_bets = {}
    while True:
        try:
            bet_string = await bot.wait_for('message', check=bet_check, timeout=20)
            placed_bets[bet_strng.author.id]
            print(f"bets placed so far: {placed_bets}")
        except asyncio.TimeoutError:
            await ctx.send("No bets received in 10 seconds. Betting is now closed.")
            break





async def options(ctx, option_string):
    parsed_options = option_string.split(';')
    option1, option2 = parsed_options[0].strip(), parsed_options[1].strip()
    print(option1, option2)

# Begin bot session
bot.run(TOKEN)