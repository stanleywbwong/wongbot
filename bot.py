# Developed by Stan

import os

import discord, asyncio
import json, re
from datetime import datetime, timedelta
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

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name=f'over {guild.name} closely'))

    # Load currency data from json
    global user_accounts
    try:
        with open('user_accounts.json') as f:
            user_accounts = json.load(f)
            print(f"loaded user amounts: {user_accounts}")
    except FileNotFoundError:
        print("Could not load user_accounts.json")
        user_accounts = {}

    print("INFO: economy commands now deprecated")


############################
###### GENERAL EVENTS ######
############################

@bot.event
async def on_member_join(member):
    guild = discord.utils.get(bot.guilds, name=GUILD)
    general = discord.utils.get(guild.channels, name='general')
    await general.send(f'{member.name} HAS BEEN ASSIMILATED.')

# TODO: refactor this, also only respond in bot-spam
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.lower() == 'wongbot awaken':
        await message.channel.send(f'WONGBOT ACTIVATED')
    
    elif 'no u' in message.content.lower():
        await message.channel.send('no u')

    elif 'casino' in message.content.lower():
        await message.channel.send(f'CASINO IS HERE')

    elif 'anime' in message.content.lower() or 'manga' in message.content.lower():
        await _ban_protocol(message, 'WEEB DETECTED', 'WEEB')

    elif 'catgirl' in message.content.lower():
        await _ban_protocol(message, 'NO CATGIRLS ALLOWED', 'DEGENERATE')

    elif 'bunnygirl' in message.content.lower():
        await _ban_protocol(message, 'NO BUNNYGIRLS ALLOWED', 'DEGENERATE')        
    
    elif 'sadge' in message.content.lower() or \
        'pog' in message.content.lower() or \
        'weirdchamp' in message.content.lower():
        await _ban_protocol(message, 'EXCESSIVE TWITCH MEMEING DETECTED', 'DEGENERATE')

    elif 'wongbot' in message.content.lower():
        if message.author.id != ADMIN:
            await message.channel.send(f'TF YOU JUST SAY ABOUT ME {message.author.name.upper()}')
        else:
            await _i_mode(message.channel)

    # TODO: Handle no kpop and kappa

    await bot.process_commands(message)

# dm invite after kicking lol
async def _ban_protocol(message, reason, offender_type):
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

async def _i_mode(channel):
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
# NOTE: Deprecated - functions moved to macaBot

# TODO: Log balance calls instead of printing
@bot.command(help='displays wongbucks balance')
async def balance(ctx):
    global user_accounts
    guild = discord.utils.get(bot.guilds, name=GUILD)
    request_id = ctx.message.author.id
    requester = discord.utils.get(guild.members, id=request_id)
    print(f"Balance requested by {request_id}: {requester.name}/{requester.nick}")
    if await _check_account(ctx, request_id):
        await ctx.send(f"BALANCE: {user_accounts[str(request_id)]['balance']} WONGBUCKS")

# TODO: Declare constants elsewhere
starting_balance = 10000
@bot.command(help='opt in to the wongbucks economy')
async def register(ctx):
    global user_accounts
    request_id = ctx.message.author.id
    if await _check_account(ctx, request_id, display_error=False):
        await ctx.send('YOU ALREADY HAVE AN ACCOUNT IDIOT')
    else:
        account = {'balance': starting_balance,
                    'name': ctx.message.author.name, 
                    'last_daily': '01/01/2000, 00:00:00'}
        user_accounts[str(request_id)] = account
        await ctx.send(f"REGISTRATION SUCCESSFUL. YOU NOW HAVE {starting_balance} WONGBUCKS")
        _save()

# TODO: Log dailies instead of printing, declare constants elsewhere
daily_amount = 2000
daily_wait = 12 # hours
@bot.command(help='d a i l y')
async def daily(ctx):
    global user_accounts
    guild = discord.utils.get(bot.guilds, name=GUILD)
    request_id = ctx.message.author.id
    requester = discord.utils.get(guild.members, id=request_id)
    print(f"Daily requested by {request_id}: {requester.name}/{requester.nick}")
    if await _check_account(ctx, request_id):
        now = datetime.now()
        last_daily = datetime.strptime(user_accounts[str(request_id)]['last_daily'], '%m/%d/%Y, %H:%M:%S')
        time_since = now - last_daily
        if time_since >= timedelta(hours=daily_wait): # TODO: Refactor constant
            await _add_balance(request_id, daily_amount)
            now_string = now.strftime('%m/%d/%Y, %H:%M:%S')
            user_accounts[str(request_id)]['last_daily'] = now_string
            await ctx.send(f'Daily collected! {daily_amount} WONGBUCKS added to your account!')
            _save()
        else:
            to_wait = timedelta(hours=daily_wait) - time_since
            hours, minutes = to_wait.seconds//3600, to_wait.seconds%3600//60
            wait_string = f"{hours} hours, {minutes} minutes" if hours else f"{minutes} minutes"
            await ctx.send(f'You must wait another {wait_string} before your next daily!')

# TODO: Log top call instead of printing
leaderboard_size=5
@bot.command(help='compete for biggest number')
async def top(ctx):
    print('got here')
    # TODO: replace with nice-looking embed (ask ron), use nicknames instead of usernames?
    def format_leaderboard(accounts, size):
        formatted_top = '-----------  LEADERBOARD  -----------\n'
        # TODO: size assumes less than size of participating accounts
        for i, account in enumerate(accounts[:size]):
            formatted_top += f"{str(i+1)}.\t {account[1]['name']}  \u2014  ${account[1]['balance']}\n"
        formatted_top += '-------------------------------------------\n'
        return formatted_top 

    global user_accounts
    guild = discord.utils.get(bot.guilds, name=GUILD)
    request_id = ctx.message.author.id
    requester = discord.utils.get(guild.members, id=request_id)
    print(f'Leaderboard requested by {request_id}: {requester.name}/{requester.nick}')
    sorted_accounts = [account_id for account_id in sorted(user_accounts.items(),\
                         key=lambda x: x[1]['balance'], reverse=True)]

    await ctx.send(format_leaderboard(sorted_accounts, leaderboard_size))


@bot.command()
async def transfer(ctx, amount: int, other: discord.Member):
    global user_accounts
    primary_id = ctx.message.author.id
    other_id = other.id
    guild = discord.utils.get(bot.guilds, name=GUILD)
    other_member = discord.utils.get(guild.members, id=other_id)
    if await _check_account(ctx, primary_id) and await _check_account(ctx, other_id):
        if await _subtract_balance(ctx, primary_id, amount):
            # TODO: Add a confirm transaction prompt
            await _add_balance(other_id, amount)
            await ctx.send(f'{amount} WONGBUCKS TRANSFERRED TO USER {other_member.nick.upper()}.')
            _save()

async def _add_balance(member_id, amount):
    global user_accounts
    user_accounts[str(member_id)]['balance'] += amount
    _save()

async def _subtract_balance(ctx, member_id, amount, display_error=True):
    global user_accounts
    current_balance = user_accounts[str(member_id)]['balance']
    if current_balance < amount or not current_balance:
        if display_error:
            await ctx.send('INSUFFICIENT FUNDS')
        return False
    user_accounts[str(member_id)]['balance'] -= amount
    _save()
    return True

async def _check_account(ctx, member_id, display_error=True):
    global user_accounts
    guild = discord.utils.get(bot.guilds, name=GUILD)
    member = discord.utils.get(guild.members, id=member_id)
    if str(member_id) not in user_accounts:
        if display_error:
            await ctx.send(f'USER "{member.nick.upper()}" DOES NOT HAVE AN ACCOUNT. REGISTER WITH $register.')
        return False
    return True

def _save():
    global user_accounts
    print(f"user_accounts saved: {user_accounts}")
    with open('user_accounts.json', 'w+') as f:
        json.dump(user_accounts, f)

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
        if msg.channel != ctx.channel or not await _check_account(ctx, msg.author.id):
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

        if not await _subtract_balance(ctx, bet_msg.author.id, amount):
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
            await _add_balance(bettor, int(winnings))

# Begin bot session
bot.run(TOKEN)