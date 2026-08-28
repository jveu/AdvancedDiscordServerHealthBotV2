import discord
from discord import app_commands
from discord.ext import commands

from ..utils.embeds import report_embed, findings_embed, history_embed

class HealthView(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Security", emoji="🛡️", style=discord.ButtonStyle.danger)
    async def security(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if not guild or guild.id != self.guild_id:
            return
        report = await self.cog.bot.auditor.run(guild)
        findings = [f for f in report["findings"] if f.severity in {"critical", "high", "medium"}]
        await interaction.response.edit_message(
            embed=findings_embed(guild, "🛡️ Security Audit", findings),
            view=self,
        )

    @discord.ui.button(label="Roles", emoji="🎭", style=discord.ButtonStyle.primary)
    async def roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if not guild or guild.id != self.guild_id:
            return
        report = await self.cog.bot.auditor.run(guild)
        findings = [f for f in report["findings"] if "role" in f.title.lower() or "administrator" in f.title.lower()]
        await interaction.response.edit_message(
            embed=findings_embed(guild, "🎭 Role Audit", findings),
            view=self,
        )

    @discord.ui.button(label="Channels", emoji="📁", style=discord.ButtonStyle.secondary)
    async def channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if not guild or guild.id != self.guild_id:
            return
        report = await self.cog.bot.auditor.run(guild)
        findings = [f for f in report["findings"] if "channel" in f.title.lower() or "categor" in f.title.lower()]
        await interaction.response.edit_message(
            embed=findings_embed(guild, "📁 Channel Audit", findings),
            view=self,
        )

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.success)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if not guild or guild.id != self.guild_id:
            return
        report = await self.cog.bot.auditor.run(guild)
        await self.cog.bot.db.save_report(guild.id, report)
        await interaction.response.edit_message(
            embed=report_embed(guild, report),
            view=self,
        )

class HealthCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Scheduler accesses config through this public attribute.
        self.bot.config = __import__("bot.config", fromlist=["settings"]).settings

    health = app_commands.Group(name="health", description="Advanced server health tools.")

    async def admin(self, interaction):
        if not interaction.guild:
            raise app_commands.CheckFailure("This command can only be used in a server.")
        if not interaction.user.guild_permissions.administrator:
            raise app_commands.CheckFailure("Administrator permission is required.")
        return True

    @health.command(name="report", description="Generate a complete interactive health report.")
    async def report(self, interaction: discord.Interaction):
        await self.admin(interaction)
        await interaction.response.defer(ephemeral=True)
        report = await self.bot.auditor.run(interaction.guild)
        await self.bot.db.save_report(interaction.guild.id, report)
        await interaction.followup.send(
            embed=report_embed(interaction.guild, report),
            view=HealthView(self, interaction.guild.id),
            ephemeral=True,
        )

    @health.command(name="score", description="Show the current health score.")
    async def score(self, interaction: discord.Interaction):
        await self.admin(interaction)
        await interaction.response.defer(ephemeral=True)
        report = await self.bot.auditor.run(interaction.guild)
        embed = report_embed(interaction.guild, report)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @health.command(name="security", description="Run a detailed security audit.")
    async def security(self, interaction: discord.Interaction):
        await self.admin(interaction)
        await interaction.response.defer(ephemeral=True)
        report = await self.bot.auditor.run(interaction.guild)
        findings = [f for f in report["findings"] if f.severity in {"critical", "high", "medium"}]
        await interaction.followup.send(
            embed=findings_embed(interaction.guild, "🛡️ Security Audit", findings),
            ephemeral=True,
        )

    @health.command(name="roles", description="Audit roles and permissions.")
    async def roles(self, interaction: discord.Interaction):
        await self.admin(interaction)
        await interaction.response.defer(ephemeral=True)
        report = await self.bot.auditor.run(interaction.guild)
        findings = [f for f in report["findings"] if "role" in f.title.lower() or "administrator" in f.title.lower()]
        await interaction.followup.send(
            embed=findings_embed(interaction.guild, "🎭 Role Audit", findings),
            ephemeral=True,
        )

    @health.command(name="channels", description="Audit channel organization and permissions.")
    async def channels(self, interaction: discord.Interaction):
        await self.admin(interaction)
        await interaction.response.defer(ephemeral=True)
        report = await self.bot.auditor.run(interaction.guild)
        findings = [f for f in report["findings"] if "channel" in f.title.lower() or "categor" in f.title.lower()]
        await interaction.followup.send(
            embed=findings_embed(interaction.guild, "📁 Channel Audit", findings),
            ephemeral=True,
        )

    @health.command(name="activity", description="Audit recent channel activity.")
    async def activity(self, interaction: discord.Interaction):
        await self.admin(interaction)
        await interaction.response.defer(ephemeral=True)
        report = await self.bot.auditor.run(interaction.guild)
        findings = [f for f in report["findings"] if "inactive" in f.title.lower() or "activity" in f.title.lower()]
        await interaction.followup.send(
            embed=findings_embed(interaction.guild, "📊 Activity Audit", findings),
            ephemeral=True,
        )

    @health.command(name="bots", description="Audit bots and integrations.")
    async def bots(self, interaction: discord.Interaction):
        await self.admin(interaction)
        await interaction.response.defer(ephemeral=True)
        report = await self.bot.auditor.run(interaction.guild)
        findings = [f for f in report["findings"] if "bot" in f.title.lower() or "webhook" in f.title.lower()]
        await interaction.followup.send(
            embed=findings_embed(interaction.guild, "🤖 Bot & Integration Audit", findings),
            ephemeral=True,
        )

    @health.command(name="history", description="Show previous health scores.")
    async def history(self, interaction: discord.Interaction):
        await self.admin(interaction)
        rows = await self.bot.db.history(interaction.guild.id, 10)
        await interaction.response.send_message(
            embed=history_embed(interaction.guild, rows),
            ephemeral=True,
        )

    config_group = app_commands.Group(name="config", description="Configure health reports.")

    @config_group.command(name="show", description="Show health bot configuration.")
    async def config_show(self, interaction: discord.Interaction):
        await self.admin(interaction)
        row = await self.bot.db.get_config(interaction.guild.id)
        channel = f"<#{row[1]}>" if row[1] else "Not configured"
        await interaction.response.send_message(
            f"**Health Configuration**\n"
            f"Report channel: {channel}\n"
            f"Alerts: {'Enabled' if row[2] else 'Disabled'}\n"
            f"Schedule: {'Enabled' if row[3] else 'Disabled'}\n"
            f"Schedule time: `{row[4]:02d}:{row[5]:02d} UTC`",
            ephemeral=True,
        )

    @config_group.command(name="channel", description="Set the report channel.")
    @app_commands.describe(channel="Channel where scheduled reports are posted.")
    async def config_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.admin(interaction)
        await self.bot.db.set_channel(interaction.guild.id, channel.id)
        await interaction.response.send_message(
            f"✅ Scheduled health reports will use {channel.mention}.",
            ephemeral=True,
        )

    @config_group.command(name="alerts", description="Enable or disable automatic alerts.")
    @app_commands.describe(enabled="Whether automatic alerts should be enabled.")
    async def config_alerts(self, interaction: discord.Interaction, enabled: bool):
        await self.admin(interaction)
        await self.bot.db.set_alerts(interaction.guild.id, enabled)
        await interaction.response.send_message(
            f"✅ Health alerts are now **{'enabled' if enabled else 'disabled'}**.",
            ephemeral=True,
        )

    @config_group.command(name="schedule", description="Configure the daily health scan.")
    @app_commands.describe(
        enabled="Enable the daily scheduled scan.",
        hour="UTC hour, 0-23.",
        minute="UTC minute, 0-59.",
    )
    async def config_schedule(self, interaction: discord.Interaction, enabled: bool, hour: int = 9, minute: int = 0):
        await self.admin(interaction)
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            await interaction.response.send_message("❌ Invalid time.", ephemeral=True)
            return
        await self.bot.db.set_schedule(interaction.guild.id, enabled, hour, minute)
        await interaction.response.send_message(
            f"✅ Daily scan is **{'enabled' if enabled else 'disabled'}** at `{hour:02d}:{minute:02d} UTC`.",
            ephemeral=True,
        )

    health.add_command(config_group)
