import discord
from discord.ext import commands
import asyncio
import inspect
from utils import *


class StickyRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        pass


    @commands.group(invoke_without_command=True,
                    description="It shows a list of sticky roles on the server.",
                    aliases=["sr", "sticky"])
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=2, type=commands.BucketType.member)
    async def sticky_roles(self, ctx):
        try:
            enabled = self.bot.sticky_roles[ctx.guild.id][0]
            sticky_roles = self.bot.sticky_roles[ctx.guild.id][1]

            if enabled:
                if sticky_roles:
                    guild_sticky_roles = ", ".join([ctx.guild.get_role(id).mention for id in sticky_roles]) + "."
                    embed = discord.Embed(description=f"Sticky roles on this server: {guild_sticky_roles}",
                                          colour=self.bot.green)
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description="No sticky roles found for this server.",
                                          colour=self.bot.green)
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description="The **Sticky Roles** module is disabled on this server.",
                                      colour=self.bot.green)
                await ctx.send(embed=embed)

        except KeyError:
            conn = await connect()
            await conn.execute(
                "INSERT INTO sticky_roles(guild_id, sticky_roles_toggle, sticky_roles_list) SELECT $1, $2, $3 WHERE NOT EXISTS (SELECT 1 FROM sticky_roles WHERE guild_id = $4)",
                ctx.guild.id, True, [], ctx.guild.id)
            await conn.close()

            self.bot.sticky_roles[ctx.guild.id] = (True, [])

            enabled = self.bot.sticky_roles[ctx.guild.id][0]
            sticky_roles = self.bot.sticky_roles[ctx.guild.id][1]

            if enabled:
                if sticky_roles:
                    guild_sticky_roles = ", ".join([ctx.guild.get_role(id).mention for id in sticky_roles]) + "."
                    embed = discord.Embed(description=f"Sticky roles on this server: {guild_sticky_roles}",
                                          colour=self.bot.green)
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description="No sticky roles found for this server.",
                                          colour=self.bot.green)
                    await ctx.send(embed=embed)

    @sticky_roles.command(description="Set the list of the sticky roles.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def set(self, ctx, *roles: Role):
        if not roles:
            raise commands.MissingRequiredArgument(inspect.Parameter("roles", inspect.Parameter.VAR_POSITIONAL))
        sticky_roles = self.bot.sticky_roles[ctx.guild.id][1]
        enabled = self.bot.sticky_roles[ctx.guild.id][0]

        if enabled:
            ids = [role.id for role in roles]

            conn = await connect()
            await conn.execute(
                "UPDATE sticky_roles SET sticky_roles_list = $1 WHERE guild_id = $2",
            ids, ctx.guild.id)
            await conn.close()

            self.bot.sticky_roles[ctx.guild.id] = (enabled, ids)

            embed = discord.Embed(title="Sticky roles list updated",
                                  description=f"Set {', '.join([role.mention for role in roles])} as the sticky role list.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="The **Sticky Roles** module is disabled on this server.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)

    @sticky_roles.command(description="Add sticky roles to the sticky role list.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def add(self, ctx, *roles: Role):
        if not roles:
            raise commands.MissingRequiredArgument(inspect.Parameter("roles", inspect.Parameter.VAR_POSITIONAL))
        sticky_roles = self.bot.sticky_roles[ctx.guild.id][1]
        enabled = self.bot.sticky_roles[ctx.guild.id][0]


        if enabled:
            ids = [role.id for role in roles if role.id not in sticky_roles]
            entered = "role"
            if len(roles) > 1:
                entered = "roles"
            if not ids:
                embed = discord.Embed(description=f"The {entered} you is already in the sticky role list.", colour=self.bot.green)
                await ctx.send(embed=embed)
                return
            added_roles = [ctx.guild.get_role(id) for id in ids]
            updated_sticky_roles = sticky_roles + ids

            conn = await connect()
            await conn.execute(
                "UPDATE sticky_roles SET sticky_roles_list = $1 WHERE guild_id = $2",
                updated_sticky_roles, ctx.guild.id)
            await conn.close()

            self.bot.sticky_roles[ctx.guild.id] = (True, updated_sticky_roles)

            embed = discord.Embed(title="Sticky roles list updated",
                                  description=f"Added {', '.join([role.mention for role in added_roles])} to the sticky role list.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="The **Sticky Roles** module is disabled on this server.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)

    @sticky_roles.command(description="Remove sticky roles from the sticky role list.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.cooldown(rate=2, per=3, type=commands.BucketType.member)
    async def remove(self, ctx, *roles: Role):
        if not roles:
            raise commands.MissingRequiredArgument(inspect.Parameter("roles", inspect.Parameter.VAR_POSITIONAL))
        sticky_roles = self.bot.sticky_roles[ctx.guild.id][1]
        enabled = self.bot.sticky_roles[ctx.guild.id][0]

        if enabled:
            ids = [role.id for role in roles if role.id in sticky_roles]
            entered = ("role", "isn't")
            if len(roles) > 1:
                entered = ("roles", "aren't")
            if not ids:
                embed = discord.Embed(description=f"The {entered[0]} you entered {entered[1]} in the sticky role list.",
                                      colour=self.bot.green)
                await ctx.send(embed=embed)
                return
            removed_roles = [ctx.guild.get_role(id) for id in ids]
            updated_sticky_roles = [role for role in sticky_roles if role not in ids]

            conn = await connect()
            await conn.execute(
                "UPDATE sticky_roles SET sticky_roles_list = $1 WHERE guild_id = $2",
                updated_sticky_roles, ctx.guild.id)
            await conn.close()

            self.bot.sticky_roles[ctx.guild.id] = (True, updated_sticky_roles)


            embed = discord.Embed(title="Sticky roles list updated",
                                  description=f"Removed {entered[0]}: {', '.join([role.mention for role in removed_roles])} from the sticky role list.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="The **Sticky Roles** module is disabled on this server.",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(StickyRoles(bot))