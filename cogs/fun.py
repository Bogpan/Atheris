import discord
from discord.ext import commands
from lyricsgenius import Genius
from utils import *

genius = Genius("ueXSAaZgaLlHJn259bL1s182HnHGQ68WBKZyEvUAtzKTFGbThsuGp0-OukMkI1mn")


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def genius(self, ctx, name, *, artist = None):
        song = genius.search_song(name, artist)

        chunks = song.lyrics.split("\n\n")

        embed = discord.Embed(title=song.title)

        for chunk in chunks:
            _type, lyrics = chunk.split("]\n")

            if len(lyrics) <= 1024:
                embed.add_field(name=f"{_type}]", value=lyrics, inline=False)
            else:
                small_chunks = [lyrics[i:i + 1024] for i in range(0, len(chunk), 1024)]

                embed.add_field(name=f"{_type}]", value=small_chunks[0], inline=False)
                small_chunks.remove(small_chunks[0])

                for c in small_chunks:
                    embed.add_field(name="...", value=c)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))