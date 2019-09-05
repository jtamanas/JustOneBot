import discord
import asyncio
import cogs
from discord.ext import commands
import cogs

# initiate bot
cmd_prefix = "!"
bot = commands.Bot(command_prefix=cmd_prefix)
from cogs.JustOne import JustOne


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print('------')


@bot.event
async def on_message(message):
    """
    This event triggers on every message received by the bot. Including one's that it sent itself.
    If you wish to have multiple event listeners they can be added in other cogs. All on_message listeners should
    always ignore bots.
    """
    if message.author.bot:
        return  # ignore all bots

    await bot.process_commands(message)


async def second_pause(ctx):
    await ctx.send("It's a-me.")
    await asyncio.sleep(4.9)
    await ctx.send("Britney")


@bot.command()
async def hello(ctx):
    await ctx.send("World")
    await second_pause(ctx)
    await asyncio.sleep(5)
    await ctx.send("Biotch")


@bot.command()
async def react(ctx):
    # emoji = discord.utils.get(bot.emojis, name='one')
    emoji_nums = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']
    for i, hint in enumerate(emoji_nums):
        await ctx.message.add_reaction(emoji_nums[i])

    reacts = ctx.message.reactions
    dels = []
    for i, react in enumerate(reacts):
        if react.count > 1:
            dels.append(i)
    print(ctx.message.reactions)
    print(dels)


@bot.command()
async def delete_me(ctx):
    await ctx.message.delete()


@bot.command()
async def get_roles(ctx):
    print(ctx.guild.roles)


@bot.command()
async def register(ctx):
    players.append(ctx.message.author)


@bot.command()
async def just_one_rules(ctx):
    embed = discord.Embed(title="Just One", description="A cooperative party game!", color=0xeee657)

    # bot commands here
    embed.add_field(name="Bot commands", value="!start to start a game \n !join to join a game before it begins")

    # rules of the game here
    embed.add_field(name="Rules", value="There are a total of 13 rounds. Each player will take turns being the guesser.")

    await ctx.send(embed=embed)


bot.load_extension("cogs.JustOne")

players = []

TOKEN = "NjE3NzU0MTEzMzIwNTUwNDk2.XWvu6w.2WKum-MpYNHtZultHeGGWTKGQJc"
bot.run(TOKEN)
