import discord
from discord.ext import commands
import asyncpg
from utils import *


class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # checks if the message isn't in DMs
        if message.guild:
            automod = self.bot.automod[message.guild.id]
            automod_modules = self.bot.automod_modules[message.guild.id]

            # checks if automod is enabled
            if automod:
                # checks if the bad word filter is enabled
                if "bwf" in automod_modules:
                    try:
                        guild_word_filter_bypass = self.bot.word_filter_bypass[message.guild.id]
                    except KeyError:
                        conn = await connect()
                        await conn.execute(
                            "INSERT INTO guild(guild_id) SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM guild WHERE guild_id = $2)",
                            message.guild.id, message.guild.id)
                        await conn.execute(
                            "INSERT INTO automod(guild_id) SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM automod WHERE guild_id = $2)",
                            message.guild.id, message.guild.id)
                        self.bot.prefixes[message.guild.id] = "."
                        await conn.close()
                        guild_word_filter_bypass = []

                    if message.author != self.bot.user:
                        if message.author.id in guild_word_filter_bypass:
                            return
                        else:
                            guild_bad_words = [bad_word.lower() for bad_word in self.bot.bad_words[message.guild.id]]
                            if guild_bad_words and message.content.lower() in guild_bad_words:
                                await message.delete()


    @commands.group(invoke_without_command=True, description="Toggles the entire automod on/off.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def automod(self, ctx):
        enabled = self.bot.automod[ctx.guild.id]
        if enabled:
            conn = await connect()
            await conn.execute("UPDATE automod SET automod_toggle = $1 WHERE guild_id = $2", False, ctx.guild.id)
            self.bot.automod[ctx.guild.id] = False
            embed = discord.Embed(title="Automod disabled", description="Automod has been disabled.", colour=self.bot.green)
            await conn.close()
        else:
            conn = await connect()
            await conn.execute("UPDATE automod SET automod_toggle = $1 WHERE guild_id = $2", True, ctx.guild.id)
            self.bot.automod[ctx.guild.id] = True
            embed = discord.Embed(title="Automod enabled", description="Automod has been enabled.",
                                  colour=self.bot.green)
            await conn.close()

        await ctx.send(embed=embed)


    @automod.group(invoke_without_command=True,
                   description="Toggles the bad word filter on/off.", aliases=["bwf", "badwordfilter"])
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def bad_word_filter(self, ctx):
        automod_modules = self.bot.automod_modules[ctx.guild.id]
        if "bwf" in automod_modules:
            self.bot.automod_modules[ctx.guild.id].remove("bwf")
            conn = await connect()
            await conn.execute("UPDATE automod SET enabled_modules = $1 WHERE guild_id = $2", self.bot.automod_modules[ctx.guild.id], ctx.guild.id)
            await conn.close()
        else:
            self.bot.automod_modules[ctx.guild.id].append("bwf")
            conn = await connect()
            await conn.execute("UPDATE automod SET enabled_modules = $1 WHERE guild_id = $2",
                               self.bot.automod_modules[ctx.guild.id], ctx.guild.id)
            await conn.close()

    @bad_word_filter.command(description="Adds a list of bad words to the filter.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def add(self, ctx, *bad_words: str):
        automod_modules = self.bot.automod_modules[ctx.guild.id]
        if "bwf" in automod_modules:
            self.bot.automod_modules[ctx.guild.id] += bad_words
            conn = await connect()
            await conn.execute("UPDATE automod SET enabled_modules = $1 WHERE guild_id = $2",
                               self.bot.automod_modules[ctx.guild.id], ctx.guild.id)
            await conn.close()
        else:
            self.bot.automod_modules[ctx.guild.id].append("bwf")
            conn = await connect()
            await conn.execute("UPDATE automod SET enabled_modules = $1 WHERE guild_id = $2",
                               self.bot.automod_modules[ctx.guild.id], ctx.guild.id)
            await conn.close()


def setup(bot):
    bot.add_cog(Automod(bot))




async def async_init():
    # connect to the database and get the guild related info
    conn = await asyncpg.connect("postgres://postgres:Dyn0SucksLOL,,RaptorAndPartsBoTBetter904@localhost:5432/Atheris")
    guild_rows = await conn.fetch(f"SELECT guild_id, prefix FROM guild")
    automod_rows = await conn.fetch("SELECT guild_id, automod_toggle, enabled_modules, bad_words, word_filter_bypass FROM automod")
    await conn.close()

    # guild options dicts
    prefixes = {}
    bad_words = {}
    word_filter_bypass = {}
    automod = {}
    automod_modules = {}

    # loop over the options for each row
    for row in guild_rows:
        values = list(row.values())
        guild_id = values[0]
        prefix = values[1]

        # set the options (for each guild)
        prefixes[guild_id] = prefix if prefix is not None else "."


    for row in automod_rows:
        values = list(row.values())
        guild_id = values[0]
        automod_toggle = values[1]
        enabled_modules = values[2]
        bad_words_list = values[3]
        word_filter_bypass_list = values[4]

        # set the options (for each guild)
        automod[guild_id] = automod_toggle
        automod_modules[guild_id] = enabled_modules if enabled_modules else []
        bad_words[guild_id] = bad_words_list if bad_words_list else []
        word_filter_bypass[guild_id] = word_filter_bypass_list if word_filter_bypass_list else []


    bot.automod = automod
    bot.automod_modules = automod_modules
    bot.prefixes = prefixes
    bot.bad_words = bad_words
    bot.word_filter_bypass = word_filter_bypass