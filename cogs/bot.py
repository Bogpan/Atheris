import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from utils import *


invite_link = "https://discord.com/api/oauth2/authorize?client_id=780406543552217119&permissions=8&redirect_uri=https%3A%2F%2Fdiscord.com%2Fapi%2Foauth2%2Fauthorize&scope=bot"


class Bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            ctx.command.reset_cooldown(ctx)
        except AttributeError:
            pass
        error = getattr(error, "original", error)
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Command on cooldown",
                                  description=f"You need to wait **{error.retry_after:.2f}s** before using this command again.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(title="Member not found", description="I can't find that member.",
                                  colour=self.bot.green,
                                  timestamp=datetime.utcnow())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = await get_usage(ctx)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="Missing permissions",
                                  description="You don't have the required permissions to do that.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = error.missing_perms
            if len(missing_perms) == 1:
                perms = f"Make sure I have the `{missing_perms[0]}` permission."
            elif len(missing_perms) == 2:
                perms = f"Make sure I have the `{missing_perms[0]}` and `{missing_perms[1]}` permissions."
            else:
                perms_list = ", ".join([f"`{perm}`" for perm in missing_perms][:-1])
                perms = f"Make sure I have the {perms_list} and `{missing_perms[-1]}` permissions."
            embed = discord.Embed(title="Missing permissions",
                                  description=f"I don't have the required permissions to do that.\n{perms}",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.ChannelNotFound):
            embed = discord.Embed(title="Channel not found",
                                  description="I can't see that channel, make sure the channel"
                                              "you entered exists and I can see it.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.RoleNotFound):
            embed = discord.Embed(title="Role not found", description="I can't find that role.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        else:
            raise error


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        conn = await connect()
        await conn.execute("INSERT INTO guild (guild_id) SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM guild WHERE guild_id = $2)",
                           guild.id, guild.id)
        self.bot.prefixes[guild.id] = "."
        await conn.close()


    @commands.command(description="Shows a list of the commands or information about a particular command.")
    async def help(self, ctx, command: str = None):
        if command is None:
            embed = discord.Embed(title="Commands", colour=self.bot.green)
            for cog in self.bot.cogs.values():
                cog_commands = [command.name for command in cog.get_commands()]
                if len(cog_commands) == 0:
                    continue
                elif len(cog_commands) == 1:
                    cog_command_list = cog_commands[0] + "."
                elif len(cog_commands) > 1:
                    cog_command_list = ", ".join(cog_commands) + "."
                embed.add_field(name=cog.qualified_name, value=cog_command_list, inline=False)
            await ctx.send(embed=embed)
        else:
            _command = self.bot.get_command(command)
            signature = _command.signature
            name = _command.name
            description = _command.description
            command_aliases = _command.aliases

            prefix = ctx.prefix

            info = ""

            if any(required in signature for required in ("<", ">")):
                info = "<> - required argument"

            if any(optional in signature for optional in ("[", "]")):
                info += "\n[] - optional argument"

            if "..." in signature:
                info += "\n... - list (needs space in-between each item)"

            if "=" in signature:
                info += "\n= - argument has a default value (default value comes after `=`)"

            if signature:
                usage = f"{prefix}{name} `{signature}`"
            else:
                usage = f"{prefix}{name}"

            aliases = "\n".join(command_aliases)
            info = f"```\n{info}\n```" if info != "" else ""

            if aliases:
                embed = discord.Embed(title=name, description=f"{info}\n**Description**\n{description}\n\n"
                                                              f"**Usage**\n{usage}\n\n**Aliases**\n{aliases}",
                                      colour=self.bot.green)
            else:
                embed = discord.Embed(title=name, description=f"{info}\n**Description**\n{description}\n\n"
                                                              f"**Usage**\n{usage}",
                                      colour=self.bot.green)
            await ctx.send(embed=embed)

    @commands.command(description="Sends the invite link for the bot so you can add it to your server.",
                      aliases=["inv"])
    @commands.cooldown(rate=3, per=2, type=commands.BucketType.member)
    @commands.cooldown(rate=2, per=1, type=commands.BucketType.member)
    async def invite(self, ctx):
        embed = discord.Embed(description=f"[Add bot]({invite_link})",
                              colour=self.bot.green)
        embed.set_footer(text="Click \"Add bot\" to be redirected.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["latency"], description="Sends the bot's latency (ping) in milliseconds.")
    @commands.cooldown(rate=3, per=1, type=commands.BucketType.member)
    async def ping(self, ctx):
        embed = discord.Embed(description=f"{int(self.bot.latency * 1000)}ms", colour=self.bot.green)
        await ctx.send(embed=embed)

    @commands.command(description="Shows info about the bot.")
    @commands.cooldown(rate=3, per=1, type=commands.BucketType.member)
    async def info(self, ctx):
        embed = discord.Embed(title="Info",
                              description=f"**Atheris** is an all-purpose bot created by Bogdan#8413 and QuaKe#5943.\n"
                                          f"For a list of commands, use `.help`. For information about a command use `.help [command]`.\n\n"
                                          f"[Add Bot]({invite_link})\n"
                                          f"[Official Bot Server](https://discord.gg/AWrZAVP8ab)",
                              colour=self.bot.green)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Bot(bot))
