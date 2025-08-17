#imports
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import torunn

#gettoken
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

#initialize logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

#set up permissions for the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.polls = True

#load extra files


bot = commands.Bot(command_prefix='/', intents=intents)

# Store active polls to track role assignments
active_polls = {}


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


required_roles = []
async def create_roles_if_needed(guild):
    """Create the required roles if they don't exist"""
    for i in [1, 2, 3]:
        for side in ['prop', 'opp', 'observer']:
            required_roles.append(f"{i} {side}")

    existing_roles = [role.name for role in guild.roles]

    for role_name in required_roles:
        if role_name not in existing_roles:
            try:
                await guild.create_role(name=role_name, mentionable=True)
                print(f"Created role: {role_name}")
            except Exception as e:
                print(f"Failed to create role {role_name}: {e}")


async def assign_role(user: discord.Member, i: int, x: str):
    guild = user.guild
    role_name = f"{i} {x}"
    role = discord.utils.get(guild.roles, name=role_name)
    # Assign role to user
    await user.add_roles(role)



# dictionary to store votes: {user_id: number}
votes = {}
room_poll_id = None
side_poll_id = None

async def choose_room(ctx):
    msg = await ctx.send("**Choose your debate room**\nReact with 1️⃣, 2️⃣, or 3️⃣")
    global room_poll_id
    room_poll_id = msg.id  # remember the poll message

    # add the reactions for voting
    options = ["1️⃣", "2️⃣", "3️⃣"]
    for emoji in options:
        await msg.add_reaction(emoji)

async def choose_side(ctx):
    msg = await ctx.send("**What side are you on?**\nReact with ✅ if on prop, ❌ if on opp, or 👁️ if observing or judging")
    global side_poll_id
    side_poll_id = msg.id  # remember the poll message

    # add the reactions for voting
    options = ["✅", "❌", "👁️"]
    for emoji in options:
        await msg.add_reaction(emoji)

@bot.event
async def on_reaction_add(reaction, user):
    """
    Saves votes when users react to the poll message.
    """
    if user.bot:
        return

    if reaction.message.id == room_poll_id:
        emoji_map = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3}
        inverse = {v: k for k, v in emoji_map.items()}
        if str(reaction.emoji) in emoji_map:
            if(user.id in votes):
                if(votes[user.id][0] != -1):
                    await reaction.message.remove_reaction(inverse[votes[user.id][0]], user)
                votes[user.id][0] = emoji_map[reaction.emoji]
            else:
                votes[user.id] = [emoji_map[str(reaction.emoji)], -1]
            print(f"{user} voted for {votes[user.id][0]}")
        else:
            await reaction.message.remove_reaction(reaction.emoji, user)

        if votes[user.id][0] != -1 and votes[user.id][1] != -1:
            await assign_role(user, votes[user.id][0], votes[user.id][1])

    if reaction.message.id == side_poll_id:
        emoji_map = {"✅": "prop", "❌": "opp", "👁️": "observer"}
        inverse = {v: k for k, v in emoji_map.items()}
        if str(reaction.emoji) in emoji_map:
            if (user.id in votes):
                if (votes[user.id][1] != -1):
                    await reaction.message.remove_reaction(inverse[votes[user.id][1]], user)
                votes[user.id][1] = emoji_map[reaction.emoji]
            else:
                votes[user.id] = [-1, emoji_map[str(reaction.emoji)]]
            print(f"{user} voted for {votes[user.id][1]}")
        else:
            await reaction.message.remove_reaction(reaction.emoji, user)

        if votes[user.id][0] != -1 and votes[user.id][1] != -1:
            await assign_role(user, votes[user.id][0], votes[user.id][1])

async def unnasign(user):
    for role in user.roles:
        for poss_role in required_roles:
            if (role.name == poss_role):
                await user.remove_roles(role)
@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return

    if reaction.message.id == room_poll_id or reaction.message.id == side_poll_id:
        emoji_map = ["1️⃣", "2️⃣" , "3️⃣"]
        if(reaction.emoji in emoji_map):
            if(user.id in votes):
                votes[user.id][0] = -1
            await unnasign(user)

    if (reaction.message.id == side_poll_id):
        emoji_map = ["✅", "❌", "👁️"]
        if (reaction.emoji in emoji_map):
            if (user.id in votes):
                votes[user.id][1] = -1
            await unnasign(user)

@bot.command()
@commands.has_permissions(administrator=True)
async def set_up_roles(ctx):
    await create_roles_if_needed(ctx.guild)
    await choose_room(ctx)
    await choose_side(ctx)
    await ctx.message.delete()

@set_up_roles.error
async def set_up_role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("haha you can't do that lol")
    else:
        await ctx.reply(f"Error: {error}")

torunn.keep_alive()
bot.run(token, log_handler = handler, log_level = logging.DEBUG)


