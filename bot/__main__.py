from .config import settings
from .database import Database
from .services.auditor import ServerAuditor
from .services.scheduler import HealthScheduler
from .cogs.health import HealthCog
import discord
from discord.ext import commands

class HealthBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.db = Database(settings.database_path)
        self.auditor = ServerAuditor()
        self.scheduler = HealthScheduler(self)

    async def setup_hook(self):
        await self.db.initialize()
        self.add_cog(HealthCog(self))
        guild = discord.Object(id=settings.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        self.scheduler.start()

    async def close(self):
        self.scheduler.stop()
        await self.db.close()
        await super().close()

bot = HealthBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Connected to {len(bot.guilds)} server(s).")

if __name__ == "__main__":
    bot.run(settings.token)
