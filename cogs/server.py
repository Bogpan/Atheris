import discord
from discord.ext import commands
from utils import *



class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        muted_role = self.bot.muted_role[member.guild.id]
        muted = self.bot.muted[member.guild.id]

        if member.id not in muted:
            if muted_role in [role.id for role in member.roles]:
                conn = await connect()
                await conn.execute("UPDATE guild SET muted = muted || $1 WHERE guild_id = $2", [member.id], member.guild.id)
                await conn.close()
                self.bot.muted[member.guild.id] = muted.append(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        muted = self.bot.muted[member.guild.id][0]
        muted_role_id = self.bot.muted_role[member.guild.id]
        muted_role = member.guild.get_role(muted_role_id)

        # checks if the member is in "rows", if he is, add the muted role to them
        if member.id == muted:
            await member.add_roles(muted_role, reason="Sticky mute role.")


    @commands.command(description="Shows the amount of members in a server. Optionally, it shows the amount of members"
                                  "with the specified role.", aliases=["membercount"])
    @commands.cooldown(rate=3, per=2, type=commands.BucketType.member)
    async def count(self, ctx, *, role: Role = None):
        if role:
            role_count = len(role.members)
            embed = discord.Embed(title=f"{role.name} member count", description=role_count, colour=role.colour)
            await ctx.send(embed=embed)
        else:
            guild_count = ctx.guild.member_count
            embed = discord.Embed(title="Member count", description=guild_count, colour=self.bot.green)
            await ctx.send(embed=embed)


    @commands.command(description="Shows info about the server.")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    async def serverinfo(self, ctx):
        guild = ctx.guild


        embed = discord.Embed(title=guild.name, colour=self.bot.green)
        embed.add_field(name="Owner", value=guild.owner.mention)

        embed.add_field(name="Member count", value=guild.member_count)
        embed.add_field(name="Role count", value=len(guild.roles))

        text = ctx.guild.text_channels
        voice = ctx.guild.voice_channels
        categories = ctx.guild.categories
        channels = ""
        if text:
            channels += f"{len(text)} text"
        if voice:
            channels += f", {len(voice)} voice"
        if categories:
            channels += f", {len(categories)} categories"
        embed.add_field(name="Channel count", value=channels)
        if guild.rules_channel:
            embed.add_field(name="Rules channel", value=guild.rules_channel.mention)

        embed.add_field(name="Region", value=str(guild.region).capitalize())

        embed.add_field(name="Boost tier", value=guild.premium_tier)
        if guild.premium_subscription_count:
            embed.add_field(name="Boost count", value=guild.premium_subscription_count)
        if guild.premium_subscribers:
            embed.add_field(name="Server boosters", value=guild.premium_subscribers)

        embed.add_field(name="Emoji count", value=f"{len(guild.emojis)}/{guild.emoji_limit}")
        embed.add_field(name="Filesize limit", value=f"{guild.filesize_limit / 1000000: .2f}MB")

        created_at = guild.created_at
        embed.add_field(name="Created at", value=f"{created_at.hour}:{created_at.minute}\n"
                                                 f"{created_at.day}/{created_at.month}/{created_at.year}")


        embed.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=embed)


    @commands.command(description="Shows the info about the specified member or the person who used the command.",
                      aliases=["whois"])
    @commands.cooldown(rate=2, per=2, type=commands.BucketType.member)
    async def memberinfo(self, ctx, *, member: Member = None):
        # if a member is specified, it sets members to that, otherwise it sets it to the author
        member = member if member else ctx.author

        embed = discord.Embed(title=str(member), colour=member.colour)

        if member.nick:
            embed.add_field(name="Nickname", value=member.nick, inline=False)

        if member.raw_status:
            if member.is_on_mobile():
                value = member.raw_status.capitalize() + " (on mobile)"
            else:
                value = member.raw_status.capitalize()

            embed.add_field(name="Status", value=value, inline=False)


        # if len(member.roles) >= 2:
        #     embed.add_field(name="Role count", value=len(member.roles))

        avatar_url = f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.png?size=1024"
        embed.add_field(name="Avatar URL", value=f"[Avatar]({avatar_url})", inline=False)

        joined_at = member.joined_at
        embed.add_field(name="Joined at", value=f"{joined_at.hour}:{joined_at.minute}\n"
                                                f"{joined_at.day}/{joined_at.month}/{joined_at.year}", inline=False)

        created_at = member.created_at
        embed.add_field(name="Created at", value=f"{created_at.hour}:{created_at.minute}\n"
                                            f"{created_at.day}/{created_at.month}/{created_at.year}", inline=False)

        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)


    @commands.command(description="Shows the profile picture (avatar) of the specified member or the person who used"
                                  "the command.", aliases=["av"])
    async def avatar(self, ctx, *, member: Member = None):
        # if a member is specified, it sets members to that, otherwise it sets it to the author
        member = member if member else ctx.author

        avatar_url = f"https://cdn.discordapp.com/avatars/{member.id}/{member.avatar}.png?size=1024"
        await ctx.send(avatar_url)

    @commands.command(description="Get the prefix for the current server or change it.")
    @commands.cooldown(rate=3, per=2, type=commands.BucketType.member)
    async def prefix(self, ctx, *, prefix: str = None):
        if prefix is None:
            prefix = self.bot.prefixes[ctx.guild.id]
            embed = discord.Embed(description=f"The prefix for this server is `{prefix}`",
                                  colour=self.bot.green)
            await ctx.send(embed=embed)
        elif prefix is not None and ctx.author.guild_permissions.manage_guild:
            if self.bot.prefixes[ctx.guild.id] and str(prefix) != self.bot.prefixes[ctx.guild.id]:
                conn = await connect()
                await conn.execute("UPDATE guild SET prefix = $1 WHERE guild_id = $2", prefix, ctx.guild.id)
                await conn.close()
                self.bot.prefixes[ctx.guild.id] = prefix
                embed = discord.Embed(title="Prefix updated",
                                      description=f"The prefix for this server is now `{prefix}`",
                                      colour=self.bot.green)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description="You are already using that prefix for this server.",
                                      colour=self.bot.green)
                await ctx.send(embed=embed)
        else:
            raise commands.MissingPermissions(["Manage Guild"])


def setup(bot):
    bot.add_cog(Server(bot))