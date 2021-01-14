import discord
from discord.ext import commands
import asyncpg
import re
import os


time_dict = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800
}


async def connect():
    # user:password@host:port/database
    conn = await asyncpg.connect(os.environ.get("atheris_postgre_login"))
    return conn


async def get_usage(ctx):
    bot = ctx.bot
    _command = ctx.command
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
                              colour=bot.green)
    else:
        embed = discord.Embed(title=name, description=f"{info}\n**Description**\n{description}\n\n"
                                                      f"**Usage**\n{usage}",
                              colour=bot.green)
    return embed


def get_member(guild, **attrs):
    name = attrs["name"]
    try:
        discriminator = attrs["discriminator"]
    except KeyError:
        discriminator = None
    user = f"{name}#{discriminator}" if discriminator else name
    for member in guild.members:
        if user.lower() in str(member).lower():
            return member


def get_role(guild, **attrs):
    name = attrs["name"]

    for role in guild.roles:
        if role.name.lower() == name.lower():
            return role


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        # time_key is the suffix, such as "s" (seconds), "m" (minutes) etc.
        time_key = argument[-1]
        amount = argument[:-1]
        try:
            time = int(amount) * time_dict[time_key]
        except KeyError:
            raise commands.BadArgument(f"{time_key} is an invalid time key.")
        except ValueError:
            raise commands.BadArgument(f"{amount} is an invalid time amount.")

        return time


class Member(commands.MemberConverter):
    async def query_member_named(self, guild, argument):
        if len(argument) > 5 and argument[-5] == '#':
            username, _, discriminator = argument.rpartition('#')
            return get_member(guild, name=username, discriminator=discriminator)
        else:
            return get_member(guild, name=argument)


class User(commands.UserConverter):
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)
        result = None
        state = ctx._state

        if match is not None:
            user_id = int(match.group(1))
            result = ctx.bot.get_user(user_id) or discord.utils.get(ctx.message.mentions, id=user_id)
            if result is None:
                try:
                    result = await ctx.bot.fetch_user(user_id)
                except discord.HTTPException:
                    raise discord.ext.commands.UserNotFound(argument) from None

            return result

        arg = argument

        # Remove the '@' character if this is the first character from the argument
        if arg[0] == '@':
            # Remove first character
            arg = arg[1:]

        # check for discriminator if it exists,
        if len(arg) > 5 and arg[-5] == '#':
            discrim = arg[-4:]
            name = arg[:-5]
            predicate = lambda u: u.name.lower() == name.lower() and u.discriminator == discrim
            result = discord.utils.find(predicate, state._users.values())
            if result is not None:
                return result

        predicate = lambda u: u.name.lower() == arg.lower()
        result = discord.utils.find(predicate, state._users.values())

        if result is None:
            raise discord.ext.commands.UserNotFound(argument)

        return result


class Role(commands.RoleConverter):
    async def convert(self, ctx, argument):
        guild = ctx.guild
        if not guild:
            raise commands.NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r'<@&([0-9]+)>$', argument)
        if match:
            result = guild.get_role(int(match.group(1)))
        else:
            result = get_role(guild, name=argument)

        if result is None:
            raise commands.RoleNotFound(argument)
        return result