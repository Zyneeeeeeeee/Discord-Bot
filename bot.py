import discord
import asyncio
import os
import aiohttp
import random
from discord.ext import commands
from config import TOKEN, API_KEY

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Turns on Bot
@bot.event
async def on_ready():
    print('Bot has Connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!help"))

# !help Command
@bot.command()
async def help(ctx):
    help_embed = discord.Embed(
        title='Help', description='List of commands', color=discord.Color.blurple())
    help_embed.add_field(
        name='!play [mention]', value='Start a game of Tic Tac Toe with another player', inline=False)
    help_embed.add_field(
        name='!weather [city]', value='Check the weather for a specific city', inline=False)
    help_embed.add_field(
        name='!invite', value='Get the invite link of the bot', inline=False)

    selection_embed = discord.Embed(
        title='Commands', description='List of commands', color=discord.Color.blurple())
    selection_embed.add_field(
        name='Games 🎮', value='''\
        `!play [mention]` - Start a game of Tic Tac Toe with another player
        ''', inline=False)
    selection_embed.add_field(
        name='Utilities ⚙', value='''\
        `!weather [city]` - Check the weather for a specific city
        `!invite` - Get the invite link of the bot
        ''', inline=False)
    selection_embed.set_footer(
        text='Powered by Discord.py', icon_url='https://wasimaster.gallerycdn.vsassets.io/extensions/wasimaster/discord-py-snippets/1.7.0/1668862916012/Microsoft.VisualStudio.Services.Icons.Default')

    await ctx.send(embed=selection_embed)

# !play Command
@bot.command()
async def play(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send('You cannot play Tic Tac Toe with yourself.')
        return
    elif member.bot:
        await ctx.send('You cannot play Tic Tac Toe with a bot.')
        return

    players = [ctx.author, member]
    symbols = ['❌', '⭕️']

    random.shuffle(players)
    random.shuffle(symbols)

    board = [['1️⃣', '2️⃣', '3️⃣'],
             ['4️⃣', '5️⃣', '6️⃣'],
             ['7️⃣', '8️⃣', '9️⃣']]

    current_player = 0

    game_embed = discord.Embed(
        title='Tic Tac Toe', description=f'{players[0].mention} vs {players[1].mention}', color=discord.Color.blurple())
    game_embed.add_field(name='Board', value='\n'.join([' '.join(row) for row in board]), inline=False)
    game_embed.set_footer(
        text=f"{players[current_player].name}'s turn ({symbols[current_player]})")

    message = await ctx.send(embed=game_embed)
    for i in range(9):
        def check(msg):
            return msg.author == players[current_player] and msg.content in ['1', '2', '3', '4', '5', '6', '7', '8', '9']

        try:
            move = await bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await message.edit(content='The game has timed out.')
            return

        move = int(move.content) - 1
        row = move // 3
        col = move % 3

        if board[row][col] == '❌' or board[row][col] == '⭕️':
            await ctx.send('That position is already taken.')
            current_player = (current_player + 1) % 2
            continue

        board[row][col] = symbols[current_player]
        game_embed.set_field_at(0, name='Board', value='\n'.join([' '.join(row) for row in board]))
        game_embed.set_footer(
            text=f"{players[(current_player + 1) % 2].name}'s turn ({symbols[(current_player + 1) % 2]})")

        await message.edit(embed=game_embed)

        if check_win(board):
            await message.edit(content=f'{players[current_player].mention} has won the game!')
            return

        if i == 8:
            await message.edit(content='The game is a tie.')
            return

        current_player = (current_player + 1) % 2


def check_win(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2]:
            return True
        if board[0][i] == board[1][i] == board[2][i]:
            return True
    if board[0][0] == board[1][1] == board[2][2]:
        return True
    if board[0][2] == board[1][1] == board[2][0]:
        return True
    return False

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Please pass in all required arguments. Type `{ctx.bot.command_prefix}help {ctx.command}` for usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument passed.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again after {error.retry_after:.2f} seconds.")
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send("This command has been disabled.")
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send(f'{ctx.command} can not be used in Direct Messages.')
        except discord.HTTPException:
            pass
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have the required permission to use this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# !invite Command
class InviteButtons(discord.ui.View):
    def __init__(self, inv: str):
        super().__init__()
        self.inv = inv
        self.add_item(discord.ui.Button(label="Invite Link", url=self.inv))

    @discord.ui.button(label="Invite Button", style=discord.ButtonStyle.blurple)
    async def inviteBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.inv, ephemeral=False)

@bot.command()
async def invite(ctx: commands.Context):
    inv = await ctx.channel.create_invite()
    await ctx.send("Click the button below to invite someone!", view= InviteButtons(str(inv)))

# !weather Command
@bot.command()
async def weather(ctx: commands.Context, *, city):  # Corrected 'commands.Contect' to 'commands.Context'
    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": API_KEY,
        "q": city
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as res:
            data = await res.json()

            location = data["location"]["name"]
            temp_c = data["current"]["temp_c"]
            temp_f = data["current"]["temp_f"]
            humidity = data["current"]["humidity"]
            wind_kph = data["current"]["wind_kph"]
            wind_mph = data["current"]["wind_mph"]  # Remove ['text'] here since 'wind_mph' is a float value, not a dictionary
            condition = data["current"]["condition"]["text"]  # Use 'text' instead of 'icon' for condition
            image_url = "http:" + data["current"]["condition"]["icon"]

            embed = discord.Embed(title=f"Weather for {location}", description=f"The condition in `{location}` is `{condition}`")
            embed.add_field(name="Temperature", value=f"C: {temp_c} | F: {temp_f}")
            embed.add_field(name="Humidity", value=f"{humidity}")
            embed.add_field(name="Wind Speeds", value=f"KPH: {wind_kph} | MPH: {wind_mph}")
            embed.set_thumbnail(url=image_url)

            await ctx.send(embed=embed)
    

bot.run(TOKEN)
