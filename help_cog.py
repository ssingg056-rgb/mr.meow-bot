import discord
from discord.ext import commands

# Keep this EMPTY [] if you want ?help to work in ALL servers!
# Or list specific IDs: [1413541161024360511, 1533591364724326551]
ALLOWED_GUILD_IDS = [
    1413541161024360511,
    1533591364724326551,
    1525429155049639977,
    1520755884693913703
]

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        # Allow everywhere if ALLOWED_GUILD_IDS is empty, otherwise restrict to list
        if ALLOWED_GUILD_IDS and (ctx.guild is None or ctx.guild.id not in ALLOWED_GUILD_IDS):
            return  

        embed = discord.Embed(
            title="🐱 Mr. Meow Help Center",
            description="Commands available in authorized servers:",
            color=discord.Color.blue()
        )
        embed.add_field(name="`?help`", value="Shows this help menu.", inline=False)
        embed.add_field(name="`mr.meow <text>` or reply", value="Talk to Mr. Meow AI.", inline=False)
        embed.add_field(name="`mr.meow send <ID> <text>`", value="Owner-only remote messaging.", inline=False)
        embed.set_footer(text="Programmed exclusively by Certified Chad")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))