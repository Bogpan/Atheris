import discord
from discord.ext import commands
from datetime import datetime
import asyncio
import asyncpg
import re
import json
import string
import random
from utils import *


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True,
                    description="Enables channel lockdown on the entire server. During lockdown, users can't send messages.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
    @commands.cooldown(rate=2, per=2, type=commands.BucketType.member)
    async def lockdown(self, ctx):
        conn = await connect()
        row = await conn.fetchrow("SELECT lockdown_channel_id, lockdown_status FROM guild WHERE guild_id = $1", ctx.guild.id)
        await conn.close()

        # info about the lockdown, such as lockdown channel id and lockdown status
        info = list(row.values())
        lockdown = info[1]
        id = info[0] if row is not None else None
        lockdown_indicator = None

        if id is None:
            embed = discord.Embed(description="There is no lockdown channel set up. You can set it up using `.lockdown set`.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        else:
            lockdown_indicator = self.bot.get_channel(id)

        if not lockdown:
            permissions = ctx.guild.default_role.permissions
            permissions.send_messages=False
            await ctx.guild.default_role.edit(reason="Lockdown initiated.",
                                              permissions=permissions)
            if id is not None:
                await lockdown_indicator.set_permissions(ctx.guild.default_role,
                                                     reason="Lockdown indicator updated.",
                                                     read_messages=True, read_message_history=True)

            # turns lockdown on in the database
            conn = await connect()
            await conn.execute("UPDATE guild SET lockdown_status = True WHERE guild_id = $1", ctx.guild.id)
            await conn.close()

            embed = discord.Embed(description="Lockdown initiated.", colour=self.bot.green)

            await ctx.send(embed=embed)
        elif lockdown:
            permissions = ctx.guild.default_role.permissions
            permissions.send_messages = True
            await ctx.guild.default_role.edit(reason="Lockdown deactivated.",
                                              permissions=permissions)
            if id is not None:
                await lockdown_indicator.set_permissions(ctx.guild.default_role,
                                                     reason="Lockdown indicator updated.",
                                                     read_messages=False, read_message_history=False)

            # turns lockdown off in the database
            conn = await connect()
            await conn.execute("UPDATE guild SET lockdown_status = False WHERE guild_id = $1", ctx.guild.id)
            await conn.close()

            embed = discord.Embed(description="Lockdown deactivated.", colour=self.bot.green)

            await ctx.send(embed=embed)

    @lockdown.command(description="Sets the lockdown channel.\nThe lockdown channel is is the channel users see (only) during"
                                  "lockdown and it's optional.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=2, type=commands.BucketType.member)
    async def set(self, ctx, channel: discord.TextChannel = None):
        channel = channel if channel is not None else ctx.channel
        conn = await connect()
        row = await conn.fetchrow(f"SELECT lockdown_channel_id FROM guild WHERE guild_id = {ctx.guild.id}")
        id = next(row.values()) if row is not None else None
        if id is None:
            await conn.execute("INSERT INTO guild(guild_id, lockdown_channel_id, lockdown_status) VALUES($1, $2, $3)",
                               ctx.guild.id, channel.id, False)
            await conn.close()
            embed = discord.Embed(description=f"Set the lockdown channel to {channel.mention}.", colour=self.bot.green)
            await ctx.send(embed=embed)
        else:
            await conn.execute("UPDATE guild SET lockdown_channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
            await conn.close()
            embed = discord.Embed(description=f"Changed the lockdown channel to {channel.mention}.", colour=self.bot.green)

            await ctx.send(embed=embed)

    @set.error
    @lockdown.error
    async def lockdown_error(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, AttributeError):
            embed = discord.Embed(title="Channel not found",
                                  description="The lockdown channel got deleted.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)


    @commands.command(description="Kick a member from the server.")
    @commands.has_guild_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def kick(self, ctx, member: Member, *, reason=""):
        if member == ctx.author or member.top_role.position >= ctx.guild.me.top_role.position or member.guild_permissions.administrator == True:
            raise commands.MissingPermissions(["Kick Members"])
        await member.send(f"**You got kicked from {ctx.guild.name}.**\n{reason}")
        await ctx.guild.kick(member, reason=reason)
        embed = discord.Embed(description=f"**{member.mention} was kicked.**\n{reason}",
                              colour=self.bot.green)
        await ctx.send(embed=embed)


    @commands.command(description="Ban a member from the server.")
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def ban(self, ctx, member: Member, *, reason=""):
        if member == ctx.author or member.top_role.position >= ctx.guild.me.top_role.position or member.guild_permissions.administrator == True:
            raise commands.MissingPermissions(["Ban Members"])
        dm = discord.Embed(description=f"**You got banned from {ctx.guild.name}.**\n{reason}",
                           colour=self.bot.green)
        await member.send(embed=dm)
        await ctx.guild.ban(member, reason=reason)
        embed = discord.Embed(description=f"**{member.mention} was banned.**\n{reason}",
                              colour=self.bot.green)
        await ctx.send(embed=embed)


    @commands.command(description="Unban a member from the server.")
    @commands.has_guild_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def unban(self, ctx, member: User, *, reason=""):
        await ctx.guild.unban(member, reason=reason)
        embed = discord.Embed(description=f"**{member} was unbanned.**\n{reason}",
                              colour=self.bot.green)
        await ctx.send(embed=embed)


    @commands.command(description="Clears the specified amount of messages in the current text channel.",
                      aliases=["purge"])
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount+1, bulk=True)

    @clear.error
    async def clear_error(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Bad argument", description="The amount you entered is invalid.",
                                  color=self.bot.green)
            await ctx.send(embed=embed)


    @commands.command(description="Mute a member from text and voice channels in the server.")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    async def mute(self, ctx, member: Member, time: TimeConverter, *, reason=""):
        if member == ctx.author or member.top_role.position >= ctx.guild.me.top_role.position or member.guild_permissions.administrator == True:
            raise commands.MissingPermissions(["Manage Roles"])

        if time > 59:
            amount = str(round(time / 60, 1))
            if amount.endswith('.0'):
                amount = amount[:-2]
            if amount == '1':
                amount = f"{amount} minute"
            else:
                amount = f"{amount} minutes"
        if time > 3599:
            amount = str(round(time / 3600, 1))
            if amount.endswith('.0'):
                amount = amount[:-2]
            if amount == '1':
                amount = f"{amount} hour"
            else:
                amount = f"{amount} hours"
        if time > 86399:
            amount = str(round(time / 86400, 1))
            if amount.endswith('.0'):
                amount = amount[:-2]
            if amount == '1':
                amount = f"{amount} day"
            else:
                amount = f"{amount} days"
        if time < 60:
            if time == 1:
                amount = f"{time} second"
            else:
                amount = f"{time} seconds"

        try:
            muted_role_id = self.bot.muted_role[ctx.guild.id]
            muted_role = ctx.guild.get_role(muted_role_id)
            if muted_role:
                pass
            else:
                raise KeyError
        except KeyError:
            muted_role = [role for role in ctx.guild.roles if "muted" in role.name.lower()]
            muted_role = muted_role[0] if muted_role else None
        if muted_role:
            conn = await connect()

            # sql command below is in testing, the commented out one is bad
            # await conn.execute(
            #     "INSERT INTO guild (muted_role_id) SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM guild WHERE muted_role_id = $2)",
            #     muted_role.id, muted_role.id)
            await conn.execute("UPDATE guild SET muted_role_id = $1 WHERE guild_id = $2", muted_role.id, ctx.guild.id)
            await conn.close()
            self.bot.muted_role[ctx.guild.id] = muted_role.id
        else:
            default_role = ctx.guild.default_role
            permissions = default_role.permissions
            permissions.send_messages = False
            permissions.connect = False
            muted_role = await ctx.guild.create_role(name="Muted", permissions=permissions, reason="Muted role created.")

            conn = await connect()

            # sql command below is in testing, the commented out one is bad
            # await conn.execute(
            #     "INSERT INTO guild (muted_role_id) SELECT $1 WHERE NOT EXISTS (SELECT 1 FROM guild WHERE guild_id = $2 AND muted_role_id = $3)",
            #     muted_role.id, ctx.guild.id, muted_role.id)
            await conn.execute("UPDATE guild SET muted_role_id = $1 WHERE guild_id = $2", muted_role.id, ctx.guild.id)
            await conn.close()
            self.bot.muted_role[ctx.guild.id] = muted_role.id

            for category in ctx.guild.categories:
                await category.set_permissions(muted_role, send_messages=False, add_reactions=False)
            for voice in ctx.guild.voice_channels:
                await voice.set_permissions(muted_role, connect=False)



        if muted_role in member.roles:
            embed = discord.Embed(title="Member is already muted", description=f"{member.mention} is already muted.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
            return

        await member.add_roles(muted_role)
        embed = discord.Embed(title="Member muted", description=f"**{member.mention} was muted for {amount}.**\n{reason}",
                              colour=self.bot.green)

        await ctx.send(embed=embed)

        dm = discord.Embed(description=f"**You got muted in {ctx.guild.name} for {amount}.**\n{reason}",
                           colour=self.bot.green)
        await member.send(embed=dm)
        await asyncio.sleep(time)
        await member.remove_roles(muted_role, reason="Mute expired.")

    @mute.error
    async def mute_error(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Invalid time", description="The time format you entered is invalid.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)


    @commands.command(description="Unmute a member from text and voice channels in the server.")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    async def unmute(self, ctx, member: Member, *, reason = ""):
        if member == ctx.author or member.top_role.position >= ctx.guild.me.top_role.position or member.guild_permissions.administrator == True:
            raise commands.MissingPermissions(["Manage Roles"])
        muted_roles = [role for role in member.roles if "muted" in role.name.lower()]
        if muted_roles:
            for role in muted_roles:
                await member.remove_roles(role)
                embed = discord.Embed(title="Member unmuted", description=f"**{member.mention} was unmuted.**\n{reason}",
                                      colour=self.bot.green)

                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Member not muted", description=f"{member.mention} is not muted.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)


    @commands.command(description="Gives the user a warning. To see the warnings of a user, use .warns.")
    @commands.has_guild_permissions(kick_members=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    async def warn(self, ctx, member: Member, *, reason=""):
        chars = string.ascii_letters + string.digits
        case_id = "".join(random.choice(chars) for x in range(15))

        now = datetime.now()
        time = now.strftime("%H:%M")
        date = now.strftime("%d.%m.%Y")
        details = {
            "moderator": ctx.author.id,
            "reason": reason,
            "case_id": case_id,
            "date": date,
            "time": time
        }
        data = json.dumps(details)
        conn = await connect()
        await conn.execute("INSERT into warns(details, warned_member_id, guild_id, case_id) VALUES ($1, $2, $3, $4)",
                           data, member.id, ctx.guild.id, case_id)
        await conn.close()
        embed = discord.Embed(title="Member warned", description=f"**{member.mention} was warned.**\n{reason}",
                              colour=self.bot.green)
        dm = discord.Embed(description=f"**You got warned in {ctx.guild.name}.**\n{reason}",
                           colour=self.bot.green)
        await ctx.send(embed=embed)
        await member.send(embed=dm)

    @commands.command(description="Delete a warning from a user.", aliases=["warnings"])
    @commands.has_guild_permissions(kick_members=True)
    @commands.cooldown(rate=2, per=2, type=commands.BucketType.member)
    async def warns(self, ctx, member: Member):
        conn = await connect()
        rows = await conn.fetch("SELECT details FROM warns WHERE guild_id = $1 AND warned_member_id = $2", ctx.guild.id, member.id)
        await conn.close()

        warns = [list(row.values())[0] for row in rows]


        if len(warns) == 0:
            embed = discord.Embed(title="No warnings found", description=f"No warnings found for {member.mention}.", colour=self.bot.green)
            await ctx.send(embed=embed)
            return
        elif len(warns) == 1:
            title = f"One case for {member}"
        else:
            title = f"{len(warns)} cases for {member}"

        embed = discord.Embed(title=title, colour=self.bot.green)

        for warn in warns:
            warn = json.loads(warn)
            case_id = warn["case_id"]
            moderator_id = warn["moderator"]
            moderator = ctx.guild.get_member(moderator_id)
            reason = warn["reason"]
            time = warn["time"]
            date = warn["date"]
            embed.add_field(name=f"__{case_id}__", value=f"Moderator: {moderator.mention} *({moderator_id})*\n"
                                                f"Reason: *{reason}*\n"
                                                f"`{time}`  `{date}`",
                            inline=False)

        await ctx.send(embed=embed)


    @commands.command(description="Deletes a warning for a member.")
    @commands.has_guild_permissions(kick_members=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    async def delwarn(self, ctx, case_id, *, reason=""):
        conn = await connect()
        row = await conn.fetchrow(f"SELECT warned_member_id, details FROM warns WHERE case_id = $1", case_id)
        await conn.execute(f"DELETE FROM warns WHERE case_id = $1", case_id)
        await conn.close()
        if row is None:
            embed = discord.Embed(title="Warning not found", description="That warning doesn't exist.", colour=self.bot.green)
            await ctx.send(embed=embed)
            return
        member_id = list(row.values())[0]
        details = list(row.values())[1]
        warn = json.loads(details)
        moderator_id = warn["moderator"]
        moderator = ctx.guild.get_member(moderator_id)
        warn_reason = warn["reason"]
        time = warn["time"]
        date = warn["date"]
        member = ctx.guild.get_member(member_id)

        embed = discord.Embed(title="Warning deleted", description=f"**Warning deleted for {member.mention}.**\n{reason}",
                              colour=self.bot.green)
        embed.add_field(name="Warning info", value=f"Moderator: {moderator.mention} *({moderator_id})*\n"
                                                f"Reason: *{warn_reason}*\n"
                                                f"`{time}`  `{date}`")

        dm = discord.Embed(description=f"**A warning in {ctx.guild.name} got deleted**\n{reason}", colour=self.bot.green)
        dm.add_field(name="Warning info", value=f"Moderator: {moderator.mention} *({moderator_id})*\n"
                                                   f"Reason: *{warn_reason}*\n"
                                                   f"`{time}`  `{date}`")


        await ctx.send(embed=embed)
        await member.send(embed=dm)


def setup(bot):
    bot.add_cog(Moderation(bot))