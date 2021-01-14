import discord
from discord.ext import commands
import asyncio
from utils import *


class Modmail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    pass



def setup(bot):
    bot.add_cog(Modmail(bot))