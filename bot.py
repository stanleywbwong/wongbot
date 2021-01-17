# Developed by Stan

import os

import discord, asyncio
import json, re
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv

# Load in environment variables, set up bot user
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN').strip('{}')
GUILD = os.getenv('DISCORD_GUILD').strip('{}')
ADMIN = int(os.getenv('SUPER_ADMIN').strip('{}'))

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
    
    if message.content.lower() == 'wongbot awaken':
        await message.channel.send(f'WONGBOT ACTIVATED')
    
    elif 'casino' in message.content.lower():
        await message.channel.send(f'CASINO IN BETA')

    elif 'anime' in message.content.lower() or 'manga' in message.content.lower():
        await ban_protocol(message, 'WEEB DETECTED', 'WEEB')

    elif 'catgirl' in message.content.lower():
        await ban_protocol(message, 'NO CATGIRLS ALLOWED', 'DEGENERATE')

    elif 'bunnygirl' in message.content.lower():
        await ban_protocol(message, 'NO BUNNYGIRLS ALLOWED', 'DEGENERATE')        
    
    elif 'sadge' in message.content.lower() or 'pog' in message.content.lower():
        await ban_protocol(message, 'EXCESSIVE TWITCH MEMEING DETECTED', 'DEGENERATE')

    # no u

    elif 'wongbot' in message.content.lower():
        if message.author.id != ADMIN:
            await message.channel.send(f'TF YOU JUST SAY ABOUT ME')
        else:
            await i_mode(message.channel)

    # no kpop

    await bot.process_commands(message)

async def ban_protocol(message, reason, offender_type):
    if message.author.guild_permissions.administrator:
        return
    await message.channel.send(f'{reason}. BAN COMMENCING IN 10 SECONDS.')
    for i in range(10, -1, -1):
        await message.channel.send(content=str(i), delete_after=1)
        await asyncio.sleep(1)
    await message.channel.send(f"TIME'S UP. GOODBYE {offender_type}", delete_after=2)

    # ban
    #await message.author.ban(delete_message_days=0)

    # kick
    await message.author.kick()

    # remove from voice
    #await message.author.edit(voice_channel=None)
    
    await message.channel.send(f'{message.author} PURGED, GOOD WORK TEAM')

async def i_mode(channel):
    print('i_mode enabled')
    while True:
        echo = input()
        if 'break' in echo:
            break
        await channel.send(echo)
    print('i_mode disabled')

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

# TODO: Log balance calls instead of printing
@bot.command(help='displays wongbucks balance')
async def balance(ctx):
    global user_amounts
    guild = discord.utils.get(bot.guilds, name=GUILD)
    request_id = ctx.message.author.id
    requester = discord.utils.get(guild.members, id=request_id)
    print(f"Balance requested by {request_id}: {requester.name}/{requester.nick}")
    if await check_account(ctx, request_id):
        await ctx.send(f"BALANCE: {user_amounts[str(request_id)]['balance']} WONGBUCKS")

# TODO: Declare constants elsewhere
starting_balance = 10000
@bot.command(help='opt in to the wongbucks economy')
async def register(ctx):
    global user_amounts
    request_id = ctx.message.author.id
    if await check_account(ctx, request_id, display_error=False):
        await ctx.send('YOU ALREADY HAVE AN ACCOUNT IDIOT')
    else:
        account = {'balance': starting_balance, 
                    'nickname': ctx.message.author.nick, 
                    'last_daily': datetime(2000, 1, 1)}
        user_amounts[str(request_id)] = account
        await ctx.send(f"REGISTRATION SUCCESSFUL. YOU NOW HAVE {starting_balance} WONGBUCKS")
        _save()

@bot.command()
async def transfer(ctx, amount: int, other: discord.Member):
    global user_amounts
    primary_id = ctx.message.author.id
    other_id = other.id
    guild = discord.utils.get(bot.guilds, name=GUILD)
    other_member = discord.utils.get(guild.members, id=other_id)
    if await check_account(ctx, primary_id) and await check_account(ctx, other_id):
        if await subtract_balance(ctx, primary_id, amount):
            # TODO: Add a confirm transaction prompt
            await add_balance(other_id, amount)
            await ctx.send(f'{amount} WONGBUCKS TRANSFERRED TO USER {other_member.nick.upper()}.')
            _save()

async def add_balance(member_id, amount):
    global user_amounts
    user_amounts[str(member_id)]['balance'] += amount
    _save()

async def subtract_balance(ctx, member_id, amount, display_error=True):
    global user_amounts
    current_balance = user_amounts[str(member_id)]['balance']
    if current_balance < amount or not current_balance:
        if display_error:
            await ctx.send('INSUFFICIENT FUNDS')
        return False
    user_amounts[str(member_id)]['balance'] -= amount
    _save()
    return True

async def check_account(ctx, member_id, display_error=True):
    global user_amounts
    guild = discord.utils.get(bot.guilds, name=GUILD)
    member = discord.utils.get(guild.members, id=member_id)
    if str(member_id) not in user_amounts:
        if display_error:
            await ctx.send(f'USER "{member.nick.upper()}" DOES NOT HAVE AN ACCOUNT. REGISTER WITH $register.')
        return False
    return True

def _save():
    global user_amounts
    print(f"user_amounts saved: {user_amounts}")
    with open('user_amounts.json', 'w+') as f:
        json.dump(user_amounts, f)

# TODO: Refactor a little
@bot.command(name='bet', help='gamble wongbucks against ur friends')
async def bet(ctx, *, question):
    
    # Checks for valid options given by the bet creator
    async def options_check(msg):
        if msg.author != ctx.author or msg.channel != ctx.channel:
            return False

        valid_options = re.compile(r".*OR.*")

        if valid_options.match(msg.content):
            return True
        else:
            await ctx.send("Enter two options, separated by 'OR', idiot")
            return False

    # Checks for valid bet given by anyone participating
    async def bet_check(msg):
        if msg.channel != ctx.channel or not await check_account(ctx, msg.author.id):
            return False

        #check this
        valid_bet = re.compile(r"bet \d+ [12]")
        
        if valid_bet.match(msg.content):
            return True
        else:
            await ctx.send("Usage: bet [amount] [1|2]")
            return False

    # Checks for valid outcome given by the bet creator
    async def outcome_check(msg):
        if msg.author != ctx.author or msg.channel != ctx.channel:
            return False

        valid_outcome = re.compile(r"outcome [12]")
        
        if valid_outcome.match(msg.content):
            return True
        else:
            await ctx.send(f'Enter "outcome 1" or "outcome 2"')
            return False

    await ctx.send(f"Question: {question}?")
    await ctx.send(f"Provide two options to bet on (separate with OR):")
    
    # Prompt for options (TODO: the check is ugly, find a fix with using the wait_for check param)
    while True:
        try:
            options_msg = await bot.wait_for('message', timeout=20)
            check = await options_check(options_msg)
            if check: break
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Try again.")
            return

    options = options_msg.content.split('OR')
    option1, option2 = options[0].strip(), options[1].strip()
    await ctx.send(f"1: {option1} \n2: {option2}")
    await ctx.send(f"TIME TO PLACE YOUR BETS. (Usage: bet [amount] [1/2])")

    # Pot values and all bets
    option1_pot, option2_pot = 0, 0 
    placed_bets = {} # {id: [option, bet]}

    # Prompt for bets until timeout (TODO: same check issue as above)
    while True:
        try:
            #print('got here')
            bet_msg = await bot.wait_for('message', timeout=30)
            check = await bet_check(bet_msg)
            if not check: continue
        except asyncio.TimeoutError:
            await ctx.send("No bets received in 20 seconds - betting closed. Awaiting outcome...")
            break

        parsed_bet = bet_msg.content.split(' ')                 
        amount, choice = int(parsed_bet[1]), int(parsed_bet[2])

        if bet_msg.author.id in placed_bets and choice != placed_bets[bet_msg.author.id][0]:
            await ctx.send("BET INVALID: You've already bet for the other option.")
            continue

        if not await subtract_balance(ctx, bet_msg.author.id, amount):
            continue

        # Update placed bets
        if bet_msg.author.id in placed_bets:
            placed_bets[bet_msg.author.id][1] += amount
        else:
            placed_bets[bet_msg.author.id] = [choice, amount]

        if choice == 1:
            option1_pot += amount
        else:
            option2_pot += amount

        pot_fraction = option1_pot/(option1_pot+option2_pot)
        
        # Display bet status
        await ctx.send(
            f"Total bet placed by {bet_msg.author.nick}: {placed_bets[bet_msg.author.id][1]}\n"
            f"Total pot: {option1_pot+option2_pot}\n"
            f"Pot split: {round(100*pot_fraction, 2)}% - {round(100*(1-pot_fraction), 2)}%"
            )

    # Resolve bets (TODO: same check issue)
    while True:
        outcome_msg = await bot.wait_for('message')
        check = await outcome_check(outcome_msg)
        if check: break

    if '1' in outcome_msg.content:
        await ctx.send(f'"{option1}" won! Wealth redistributed.')
        winner, winning_pot, losing_pot = 1, option1_pot, option2_pot
    else:
        await ctx.send(f'"{option2}" won! Wealth redistributed.')
        winner, winning_pot, losing_pot = 2, option2_pot, option1_pot

    for bettor in placed_bets.keys():
        if placed_bets[bettor][0] == winner:
            winnings = placed_bets[bettor][1] + (placed_bets[bettor][1]/winning_pot*losing_pot)
            await add_balance(bettor, int(winnings))

# Begin bot session
bot.run(TOKEN)