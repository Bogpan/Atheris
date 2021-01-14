import discord
from discord.ext import commands
import asyncio
from utils import *


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot




def setup(bot):
    bot.add_cog(Settings(bot))
