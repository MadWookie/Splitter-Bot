import asyncpg

from discord.ext import commands
import discord

from utils import checks


class Mod:
    def __init__(self, bot):
        self.bot = bot

###################
#                 #
# JOIN CHECK      #
#                 #
###################

    @checks.db
    async def on_member_join(self, member):
        async with self.bot.db_pool.acquire() as con:
            ban = await con.fetchrow('''
                SELECT * FROM bans WHERE user_id = $1
                ''', member.id)
        try:
            if ban['user_id'] is not None:
                await member.ban(reason="Previously Banned")
        except:
            pass

###################
#                 #
# BANNING         #
#                 #
###################

    @checks.db
    @commands.is_owner()
    @commands.command(name='ban', aliases=['fuck'])
    async def user_ban(self, ctx, user: discord.Member, reason: str='Breaking Rules.'):
        """Adds a user to the bot's banlist"""
        try:
            async with ctx.con.transaction():
                await ctx.con.execute('''
                    INSERT INTO bans (user_id) VALUES ($1)
                    ''', user.id)
        except asyncpg.UniqueViolationError:
            await ctx.send('**{0.name}** is already banned.'.format(user), delete_after=15)
        else:
            await ctx.send("Banned user {0.name}({0.id}) due to **{1}**.".format(user, reason))
            for guild in self.bot.guilds:
                m = guild.get_member(user.id)
                if m is not None:
                    await m.ban(reason=reason)

###################
#                 #
# UNBANNING       #
#                 #
###################

    @checks.db
    @commands.is_owner()
    @commands.command(name='unban', aliases=['unfuck'])
    async def user_unban(self, ctx, user_id: int, reason: str='Appealed.'):
        """Removes a user from the bot's banlist"""
        async with ctx.con.transaction():
            res = await ctx.con.execute('''
                DELETE FROM bans WHERE user_id = $1
                ''', user_id)
        deleted = int(res.split()[-1])
        if deleted:
            user = await self.bot.get_user_info(user_id)
            for guild in self.bot.guilds:
                try:
                    await guild.unban(user)
                except discord.HTTPException:
                    pass
            await ctx.send("Unbanned user {0} due to **{1}**.".format(user, reason))
        else:
            await ctx.send('**{0}** is not banned.'.format(user), delete_after=15)


def setup(bot):
    bot.add_cog(Mod(bot))
