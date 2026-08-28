import asyncio
from datetime import datetime, timezone
import discord

class HealthScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.task = None

    def start(self):
        if self.task is None:
            self.task = asyncio.create_task(self.loop())

    def stop(self):
        if self.task:
            self.task.cancel()
            self.task = None

    async def loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = datetime.now(timezone.utc)
                guild = self.bot.get_guild(self.bot.config.guild_id) if hasattr(self.bot, "config") else None
                # Scheduling is intentionally lightweight; configuration is stored in DB.
                if guild:
                    config = await self.bot.db.get_config(guild.id)
                    enabled = bool(config[3])
                    hour, minute = config[4], config[5]
                    if enabled and now.hour == hour and now.minute == minute:
                        report = await self.bot.auditor.run(guild)
                        await self.bot.db.save_report(guild.id, report)
                        if config[1]:
                            channel = guild.get_channel(config[1])
                            if channel:
                                from ..utils.embeds import report_embed
                                await channel.send(
                                    content="📊 **Scheduled Server Health Report**",
                                    embed=report_embed(guild, report),
                                )
                        await asyncio.sleep(61)
            except asyncio.CancelledError:
                return
            except Exception as exc:
                print(f"Scheduler error: {exc}")
            await asyncio.sleep(30)
