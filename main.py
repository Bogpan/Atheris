import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncpg
import asyncio
from utils import *


async def _get_prefix(bot, message):
    guild_prefix = "."
    if message.guild is not None:
        try:
            guild_prefix = bot.prefixes[message.guild.id]
        except KeyError:
            conn = await connect()
            await conn.execute(
                "INSERT INTO guild(guild_id) SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM guild WHERE guild_id = $2)",
                message.guild.id, message.guild.id)
            await conn.close()
    return commands.when_mentioned_or(guild_prefix)(bot, message)


async def async_init():
    # connect to the database and get the guild related info
    conn = await asyncpg.connect("postgres://postgres:Dyn0SucksLOL,,RaptorAndPartsBoTBetter904@localhost:5432/Atheris")
    guild_rows = await conn.fetch("SELECT guild_id, prefix, muted_role_id, muted FROM guild")
    await conn.close()

    # guild options dicts
    prefixes = {}
    muted_role = {}
    muted = {}

    # loop over the options for each row
    for row in guild_rows:
        values = list(row.values())
        guild_id = values[0]
        prefix = values[1]
        muted_role_id = values[2]
        guild_muted = values[3]

        # set the options (for each guild)
        prefixes[guild_id] = prefix if prefix is not None else "."
        muted_role[guild_id] = muted_role_id if muted_role_id else None
        muted[guild_id] = guild_muted

    bot.prefixes = prefixes
    bot.muted_role = muted_role
    bot.muted = muted

intents = discord.Intents.all()
allowed_mentions = discord.AllowedMentions.none()
activity = discord.Activity(name='.info', type=discord.ActivityType.playing)
bot = commands.Bot(command_prefix=_get_prefix, intents=intents, max_messages=20000, case_insensitive=True,
                   help_command=None, activity=activity, allowed_mentions=allowed_mentions)
bot.loop.create_task(async_init())


bot.owner_ids = [287256464047865857, 405798011172814868]
bot.green = discord.Colour(0x30c21d)


def check_ownership(ctx):
    return ctx.author.id in bot.owner_ids


@bot.event
async def on_ready():
    print("Atheris is starting...")
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            filename = file.replace(".py", "")
            try:
                bot.load_extension(f"cogs.{filename}")
                print(f"Loaded [cogs.{filename}]")
            except commands.NoEntryPointError:
                print(f"[cogs.{filename}] doesn't have a setup function.")
    print("Atheris is ready.")


@bot.command(hidden=True)
@commands.check(check_ownership)
async def load(ctx, cog: str):
    check = "✅"
    if cog == "_all":
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename.replace(".py", "")
                bot.load_extension(f"cogs.{name}")
        await ctx.message.add_reaction(check)
    else:
        bot.load_extension(f"cogs.{cog}")
        await ctx.message.add_reaction(check)


@bot.command(aliases=["un"], hidden=True)
@commands.check(check_ownership)
async def unload(ctx, cog: str):
    check = "✅"
    if cog == "_all":
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename.replace(".py", "")
                bot.unload_extension(f"cogs.{name}")
        await ctx.message.add_reaction(check)
    else:
        bot.unload_extension(f"cogs.{cog}")
        await ctx.message.add_reaction(check)


@bot.command(aliases=["re"], hidden=True)
@commands.check(check_ownership)
async def reload(ctx, cog: str):
    check = "✅"
    if cog == "_all":
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                name = filename.replace(".py", "")
                bot.reload_extension(f"cogs.{name}")
        await ctx.message.add_reaction(check)
    else:
        bot.reload_extension(f"cogs.{cog}")
        await ctx.message.add_reaction(check)


@bot.command(aliases=["cogs", "list"], hidden=True)
@commands.check(check_ownership)
async def list_cogs(ctx):
    await ctx.message.delete()
    cogs_base = []
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            cogs_base.append(filename)
    cogs = [cog.replace(".py", "") for cog in cogs_base]
    cogs_list = "\n".join(cogs)
    await ctx.send(f"```\n{cogs_list}\n```")


@reload.error
async def reload_error(ctx, error):
    error = getattr(error, "original", error)
    failed = "❌"
    failed1 = "✖"
    await ctx.message.add_reaction(failed)
    if isinstance(error, commands.ExtensionNotLoaded):
        await ctx.send("Extension(s) not loaded.")
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("Extension(s) not found.")
    elif isinstance(error, commands.ExtensionError):
        await ctx.send("Extension(s) error.")
        await ctx.send(error)
    elif isinstance(error, commands.ExtensionFailed):
        await ctx.send("Extension(s) failed.")
        await ctx.send(error)


@load.error
async def load_error(ctx, error):
    error = getattr(error, "original", error)
    failed = "❌"
    failed1 = "✖"
    await ctx.message.add_reaction(failed)
    if isinstance(error, commands.ExtensionAlreadyLoaded):
        await ctx.send("Extension(s) already loaded.")
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("Extension(s) not found.")
    elif isinstance(error, commands.ExtensionError):
        await ctx.send("Extension(s) error.")
        await ctx.send(error)
    elif isinstance(error, commands.ExtensionFailed):
        await ctx.send("Extension(s) failed.")
        await ctx.send(error)


@unload.error
async def unload_error(ctx, error):
    error = getattr(error, "original", error)
    failed = "❌"
    failed1 = "✖"
    await ctx.message.add_reaction(failed)
    if isinstance(error, commands.ExtensionNotLoaded):
        await ctx.send("Extension(s) not loaded.")
    elif isinstance(error, commands.ExtensionNotFound):
        await ctx.send("Extension(s) not found.")
    elif isinstance(error, commands.ExtensionError):
        await ctx.send("Extension(s) error.")
        await ctx.send(error)
    elif isinstance(error, commands.ExtensionFailed):
        await ctx.send("Extension(s) failed.")
        await ctx.send(error)


bot.run(os.environ.get("atheris_token"))