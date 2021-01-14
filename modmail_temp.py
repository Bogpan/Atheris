import discord
from discord.ext import commands, tasks
import asyncio
import aiosqlite
from datetime import datetime
green = discord.Colour(0x30c21d)

class Modmail(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def update_db(self): # backs up botvars to database
        conn = await aiosqlite.connect("bot.db")
        cursor = await conn.execute("UPDATE botvars SET activetickets = ?, settinguptickets = ? WHERE number = ?", (str(self.bot.activetickets), str(self.bot.settinguptickets), "1"))
        info = await cursor.fetchall()
        await conn.commit()
        await conn.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and not message.author == self.bot.user and not message.content.startswith(','):
            if not message.author.id in self.bot.activetickets and not message.author.id in self.bot.settinguptickets:
                item = None
                self.bot.settinguptickets.append(message.author.id)
                await self.update_db()
                old_mutual_guilds = [guild for guild in self.bot.guilds if guild.get_member(message.author.id)] # gets mutual guilds
                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute("SELECT * from modmail")
                info = await cursor.fetchall() # fetches guilds with modmail set up
                await conn.commit()
                await conn.close()
                mutual_guilds = []
                for guild in old_mutual_guilds: # only selects mutual guilds which has modmail set up
                    for item in info:
                        if item[0] == guild.id:
                            mutual_guilds.append(guild)
                if len(mutual_guilds) > 0: # user selects server prompt
                    if len(mutual_guilds) > 10:
                        description = ''
                        for i in range(len(mutual_guilds)):
                            description = f"{description}\n{i + 1}. **{mutual_guilds[i].name}**"
                        embed_msg = discord.Embed(title="Modmail",
                                                  description=f"Please select the server you wish to contact. Send the number in chat corresponding to the server's number.\n{description}", color=green)
                        send = await message.channel.send(embed=embed_msg)
                        numbers = [str(i + 1) for i in range(len(mutual_guilds))]
                        def check(checkmessage):
                            return checkmessage.author == message.author and checkmessage.content in numbers
                        try:
                            checkmessage = await self.bot.wait_for('message', check=check, timeout=60)
                        except asyncio.TimeoutError:
                            self.bot.settinguptickets.remove(message.author.id)
                            await self.update_db()
                            embed_msg = discord.Embed(title="Timed Out", description="You failed to send a valid number in time.", colour=green)
                            await send.edit(embed=embed_msg)
                            item = None
                        else:
                            item = int(checkmessage.content)-1
                    else:
                        description = ''
                        for i in range(len(mutual_guilds)):
                            description = f"{description}\n{i + 1}. **{mutual_guilds[i].name}**"
                        embed_msg = discord.Embed(title="Modmail",
                                                  description=f"Please select the server you wish to contact. React on the number corresponding to the server's number.\n{description}", color=green)
                        send = await message.channel.send(embed=embed_msg)
                        reactions = ["1\N{variation selector-16}\N{combining enclosing keycap}",
                                     "2\N{variation selector-16}\N{combining enclosing keycap}",
                                     "3\N{variation selector-16}\N{combining enclosing keycap}",
                                     "4\N{variation selector-16}\N{combining enclosing keycap}",
                                     "5\N{variation selector-16}\N{combining enclosing keycap}",
                                     "6\N{variation selector-16}\N{combining enclosing keycap}",
                                     "7\N{variation selector-16}\N{combining enclosing keycap}",
                                     "8\N{variation selector-16}\N{combining enclosing keycap}",
                                     "9\N{variation selector-16}\N{combining enclosing keycap}",
                                     "\N{keycap ten}",
                                     "\u274C"]
                        for i in range(len(mutual_guilds)):
                            await send.add_reaction(reactions[i])
                        await send.add_reaction(reactions[-1])
                        def check(reaction, user):
                            return user == message.author and str(reaction.emoji) in reactions
                        try:
                            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=5)
                        except asyncio.TimeoutError:
                            embed_msg = discord.Embed(title="Timed Out", description="You failed to react on the message in time.", colour=green)
                            await send.edit(embed=embed_msg)
                            self.bot.settinguptickets.remove(message.author.id)
                            await self.update_db()
                        else:
                            if not str(reaction.emoji) == reactions[-1]:
                                item = reactions.index(str(reaction.emoji))
                            else:
                                self.bot.settinguptickets.remove(message.author.id)
                                await self.update_db()
                                await send.delete()
                    if item != None:
                        try:
                            embed_msg = discord.Embed(title=f"Modmail Ticket Created in {mutual_guilds[item].name}",
                                                      description="If you send messages here, they will be able to see them on the other end.\nUse the `leave` command to leave the conversation.",
                                                      colour=green)
                            await send.delete()
                            await message.channel.send(embed=embed_msg)
                            for row in info:
                                if row[0] == mutual_guilds[item].id:
                                    serverrow = row
                                    break
                            guild = self.bot.get_guild(mutual_guilds[item].id)
                            category = guild.get_channel(serverrow[1])
                            logging = guild.get_channel(serverrow[2])
                            embed_msg = discord.Embed(colour=green)
                            embed_msg.set_author(name=f"{message.author}: Ticket Created", icon_url=message.author.avatar_url)
                            try:
                                await logging.send(embed=embed_msg)
                            except:
                                pass
                            time = datetime.utcnow()
                            formattedtime = time.strftime("%c")
                            timezone = time.strftime("%Z")
                            channel = await guild.create_text_channel(str(message.author), category=category,
                                                                      topic=f"{formattedtime} {timezone}")
                            attachments = message.attachments
                            found = False
                            if len(attachments) > 0:
                                for attachment in message.attachments:
                                    if attachment.filename.endswith('jpeg') or attachment.filename.endswith(
                                            'png') or attachment.filename.endswith('jpg') or attachment.filename.endswith(
                                            'gif'):
                                        if found is False:
                                            attachmenttouse = attachment
                                            found = True
                            embed_msg = discord.Embed(title=f"Ticket Created",
                                                      description="Use the `close` command in this channel to close this ticket.",
                                                      colour=green)
                            embed_msg.set_author(name=message.author, icon_url=message.author.avatar_url)
                            await channel.send(embed=embed_msg)
                            embed_msg = discord.Embed(description=message.content[:1950], colour=green)
                            embed_msg.set_author(name=message.author, icon_url=message.author.avatar_url)
                            if found is True:
                                embed_msg.set_image(url=attachmenttouse.url)
                            await channel.send(embed=embed_msg)
                            try:
                                await message.add_reaction("✅")
                            except:
                                pass
                            self.bot.activetickets[message.author.id] = f"{mutual_guilds[item].id}:{channel.id}"
                            await self.update_db()
                            self.bot.settinguptickets.remove(message.author.id)
                            await self.update_db()
                        except TypeError:
                            pass
            else:
                ctx = await self.bot.get_context(message)
                if ctx.valid is False:
                    try:
                        value = self.bot.activetickets[message.author.id] # user sent message
                        ids = value.split(':')
                        attachments = message.attachments
                        found = False
                        if len(attachments) > 0:
                            for attachment in message.attachments:
                                if attachment.filename.endswith('jpeg') or attachment.filename.endswith(
                                        'png') or attachment.filename.endswith('jpg') or attachment.filename.endswith('gif'):
                                    if found is False:
                                        attachmenttouse = attachment
                                        found = True
                        embed_msg = discord.Embed(description=message.content[:1950], colour=green)
                        embed_msg.set_author(name=message.author, icon_url=message.author.avatar_url)
                        if found is True:
                            embed_msg.set_image(url=attachmenttouse.url)
                        guild = self.bot.get_guild(int(ids[0]))
                        channel = guild.get_channel(int(ids[1]))
                        try:
                            await channel.send(embed=embed_msg)
                            try:
                                await message.add_reaction("✅")
                            except:
                                pass
                        except AttributeError:
                            self.bot.activetickets.pop(message.author.id)
                            await self.update_db()
                            embed_msg = discord.Embed(title=f"Ticket Closed in {guild.name}", description='No reason provided.', colour=green)
                            await message.channel.send(embed=embed_msg)
                    except KeyError:
                        pass
        elif not message.guild is None and not message.author == self.bot.user: # mods in guild sent message
            for key in self.bot.activetickets:
                ids = self.bot.activetickets[key].split(':')
                if message.channel.id == int(ids[1]):
                    user = self.bot.get_user(key)
                    ctx = await self.bot.get_context(message)
                    if ctx.valid is False:
                        attachments = message.attachments
                        found = False
                        if len(attachments) > 0:
                            for attachment in message.attachments:
                                if attachment.filename.endswith('jpeg') or attachment.filename.endswith('png') or attachment.filename.endswith('jpg') or attachment.filename.endswith('gif'):
                                    if found is False:
                                        attachmenttouse = attachment
                                        found = True
                        embed_msg = discord.Embed(description=message.content[:1950], colour=green)
                        embed_msg.set_author(name=message.author, icon_url=message.author.avatar_url)
                        if found is True:
                            embed_msg.set_image(url=attachmenttouse.url)
                        try:
                            await user.send(embed=embed_msg)
                            try: # in case bot doesn't have reaction perms
                                await message.add_reaction("✅")
                            except:
                                pass
                        except: # message failed to send
                            embed_msg = discord.Embed(title="Message Failed",
                                                      description="Unable to send message to that user.", colour=green)
                            await message.channel.send(embed=embed_msg)
                            try:
                                await message.add_reaction("❌")
                            except:
                                pass
                        break

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setupmodmail(self, ctx):
        bot_member = ctx.message.guild.get_member(self.bot.user.id)
        if bot_member.guild_permissions.manage_channels is True:
            conn = await aiosqlite.connect("bot.db")
            cursor = await conn.execute("SELECT * from modmail")
            info = await cursor.fetchall()
            await conn.commit()
            await conn.close()
            found = False
            for row in info:
                if row[0] == ctx.message.guild.id:
                    found = True
                    rowdata = row
                    break
            if found is False:
                category = await ctx.guild.create_category("Modmail")
                embed_msg = discord.Embed(title=f"Sucessfully set up Modmail category.", description="When someone contacts Modmail by DMing me and selecting this server, a ticket will be created in that category.\n\n**NOTE:** Make sure to check the permissions for that category because everyone might be able to see it.", colour=green)
                await ctx.send(embed=embed_msg)
                channel = await ctx.guild.create_text_channel("Modmail Logging", category=category)
                embed_msg = discord.Embed(title="This channel category has been configured for Modmail.", description="When someone contacts Modmail by DMing me and selecting this server, a ticket will be created in this category.\nTicket creation and creation will be logged here.", colour=green)
                await channel.send(embed=embed_msg)
                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute("INSERT INTO modmail VALUES (?, ?, ?)", (ctx.guild.id, category.id, channel.id))
                await conn.commit()
                await conn.close()
            else:
                embed_msg = discord.Embed(title="You already have Modmail set up!", description="Use the `disablemodmail` commmand to disable it.", colour=green)
                await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="I don't have the nessesary permissions to do that.", description="I require the `Manage Channels` permission.", colour=green)
            await ctx.send(embed=embed_msg)

    @commands.command()
    async def disablemodmail(self, ctx):
        bot_member = ctx.message.guild.get_member(self.bot.user.id)
        if bot_member.guild_permissions.manage_channels is True:
            conn = await aiosqlite.connect("bot.db")
            cursor = await conn.execute("SELECT * from modmail")
            info = await cursor.fetchall()
            await conn.commit()
            await conn.close()
            found = False
            for row in info:
                if row[0] == ctx.message.guild.id:
                    found = True
                    rowdata = row
                    break
            if found is True:
                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute(f"DELETE FROM modmail WHERE guildid = '{ctx.message.guild.id}'")
                await conn.commit()
                await conn.close()
                embed_msg = discord.Embed(title="Successfully disabled modmail for this server.", description="Use the `setupmodmail` commmand to re-enable it.", colour=green)
                await ctx.send(embed=embed_msg)
                try:
                    category = ctx.guild.get_channel(rowdata[1])
                    channel = ctx.guild.get_channel(rowdata[2])
                    await channel.delete()
                    await category.delete()
                except:
                    pass
            else:
                embed_msg = discord.Embed(title="You don't have Modmail set up!",
                                          description="Use the `setupmodmail` commmand to enable it.", colour=green)
                await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="I don't have the nessesary permissions to do that.",
                                      description="I require the `Manage Channels` permission.", colour=green)
            await ctx.send(embed=embed_msg)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def close(self, ctx, *, reason=None):
        try:
            worked = False
            for key in self.bot.activetickets:
                ids = self.bot.activetickets[key].split(':')
                if ctx.message.channel.id == int(ids[1]):
                    worked = True
                    if ctx.author.guild_permissions.manage_channels is True:
                        user = self.bot.get_user(key)
                        self.bot.activetickets.pop(key)
                        await self.update_db()
                        if reason is None:
                            embed_msg = discord.Embed(title=f"Ticket Closed in {ctx.guild.name}", description="No reason provided.", colour=green)
                        else:
                            embed_msg = discord.Embed(title=f"Ticket Closed in {ctx.guild.name}", description=reason[:1950], colour=green)
                        try:
                            embed_msg.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
                            await user.send(embed=embed_msg)
                            guild = self.bot.get_guild(int(ids[0]))
                            channel = guild.get_channel(int(ids[1]))
                            await channel.delete()
                            conn = await aiosqlite.connect("bot.db")
                            cursor = await conn.execute("SELECT * from modmail")
                            info = await cursor.fetchall()
                            await conn.commit()
                            await conn.close()
                            for row in info:
                                if row[0] == ctx.guild.id:
                                    serverrow = row
                                    break
                            logging = ctx.guild.get_channel(int(serverrow[2]))
                            embed_msg = discord.Embed(description=f"Closed by: {ctx.message.author.mention}", colour=green)
                            embed_msg.set_author(name=f"{user}: Ticket Closed", icon_url=user.avatar_url)
                            try:
                                await logging.send(embed=embed_msg)
                            except:
                                pass
                        except:
                            pass
                    else:
                        embed_msg = discord.Embed(title="You don't have permission to use that command!",
                                                  description="You need `Manage Channels`.", colour=green)
                        await ctx.send(embed=embed_msg)
                        break
            if worked is False:
                embed_msg = discord.Embed(title="You're not in an active modmail ticket!", description="This command only works in a server. If you're in a DM, use the `leave` command instead.", colour=green)
                await ctx.send(embed=embed_msg)
        except:
            pass

    @commands.command()
    async def leave(self, ctx):
        try:
            worked = False
            for key in self.bot.activetickets:
                if key == ctx.message.author.id and ctx.guild is None: # user left conversation
                    worked = True
                    ids = [int(id) for id in self.bot.activetickets[key].split(":")]
                    guild = self.bot.get_guild(ids[0])
                    channel = guild.get_channel(ids[1])
                    embed_msg = discord.Embed(title=f"{ctx.message.author} has left this conversation.", description="This channel is now archived. Delete the channel to get rid of this ticket, or use the `cleararchived` commands to delete all archived channels.", colour=green)
                    self.bot.activetickets.pop(key)
                    await self.update_db()
                    await channel.send(embed=embed_msg)
                    try:
                        await channel.edit(name=f"archived {channel.name}")
                    except:
                        pass
                    embed_msg = discord.Embed(title="You left this conversation.", description="Open a new ticket for that server in order to send messages to them again.", colour=green)
                    await ctx.send(embed=embed_msg)
                    conn = await aiosqlite.connect("bot.db")
                    cursor = await conn.execute("SELECT * from modmail")
                    info = await cursor.fetchall()
                    await conn.commit()
                    await conn.close()
                    for row in info:
                        if row[0] == guild.id:
                            serverrow = row
                            break
                    logging = guild.get_channel(int(serverrow[2]))
                    embed_msg = discord.Embed(colour=green)
                    embed_msg.set_author(name=f"{ctx.message.author}: Left Conversation", icon_url=ctx.message.author.avatar_url)
                    try:
                        await logging.send(embed=embed_msg)
                    except:
                        pass
                    break
                elif int(self.bot.activetickets[key].split(":")[1]) == ctx.message.channel.id: # guild mods left conversation
                    worked = True
                    if ctx.author.guild_permissions.manage_channels is True:
                        user = self.bot.get_user(key)
                        embed_msg = discord.Embed(title=f"{ctx.guild.name} have left this conversation.", description="Open a new ticket for that server in order to send messages to them again.", colour=green)
                        self.bot.activetickets.pop(key)
                        await self.update_db()
                        await user.send(embed=embed_msg)
                        try:
                            await ctx.message.channel.edit(name=f"archived {ctx.message.channel.name}")
                        except:
                            pass
                        embed_msg = discord.Embed(title="You left this conversation.", description="This channel is now archived. Delete the channel to get rid of this ticket, or use the `cleararchived` commands to delete all archived channels.", colour=green)
                        await ctx.send(embed=embed_msg)
                        conn = await aiosqlite.connect("bot.db")
                        cursor = await conn.execute("SELECT * from modmail")
                        info = await cursor.fetchall()
                        await conn.commit()
                        await conn.close()
                        for row in info:
                            if row[0] == ctx.guild.id:
                                serverrow = row
                                break
                        logging = ctx.guild.get_channel(int(serverrow[2]))
                        embed_msg = discord.Embed(colour=green, description=f"Left by: {ctx.message.author.mention}")
                        embed_msg.set_author(name=f"{user}: Server Left Conversation", icon_url=user.avatar_url)
                        try:
                            await logging.send(embed=embed_msg)
                        except:
                            pass
                        break
                    else:
                        embed_msg = discord.Embed(title="You don't have permission to use that command!", description="You need `Manage Channels`.", colour=green)
                        await ctx.send(embed=embed_msg)
                        break
            if worked is False:
                embed_msg = discord.Embed(title="You're not in an active modmail ticket!", colour=green)
                await ctx.send(embed=embed_msg)
        except RuntimeError:
            pass

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def cleararchived(self, ctx):
        bot_member = ctx.message.guild.get_member(self.bot.user.id)
        if bot_member.guild_permissions.manage_channels is True:
            conn = await aiosqlite.connect("bot.db")
            cursor = await conn.execute("SELECT * from modmail")
            info = await cursor.fetchall()
            await conn.commit()
            await conn.close()
            found = False
            for row in info:
                if row[0] == ctx.message.guild.id:
                    found = True
                    serverrow = row
                    break
            if found is True:
                category = ctx.message.guild.get_channel(serverrow[1])
                clearedchannels = 0
                for channel in category.text_channels:
                    if channel.name.startswith("archived"):
                        await channel.delete()
                        clearedchannels += 1
                if clearedchannels > 0:
                    embed_msg = discord.Embed(title=f"Cleared {clearedchannels} archived ticket(s).", colour=green)
                    logging = ctx.message.guild.get_channel(serverrow[2])
                    embed_msg2 = discord.Embed(colour=green)
                    embed_msg2.set_author(
                        name=f"{ctx.message.author}: Cleared {clearedchannels} archived Modmail ticket(s)",
                        icon_url=ctx.message.author.avatar_url)
                    try:
                        await logging.send(embed=embed_msg2)
                    except:
                        pass
                else:
                    embed_msg = discord.Embed(title=f"Couldn't find any archived text channels in the modmail category.", colour=green)
                try:
                    await ctx.send(embed=embed_msg)
                except:
                    try:
                        await ctx.message.author.send(embed=embed_msg)
                    except:
                        pass
            else:
                embed_msg = discord.Embed(title="This server doesn't have Modmail set up!", colour=green)
                await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="I don't have the required permissions to do that!", description="I need `Manage Channels` to perform that action.", colour=green)
            await ctx.send(embed=embed_msg)



def setup(bot):
    bot.add_cog(Modmail(bot))