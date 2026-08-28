from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import discord

@dataclass
class Finding:
    severity: str
    title: str
    detail: str
    recommendation: str

class ServerAuditor:
    async def run(self, guild: discord.Guild):
        findings = []
        security = 100
        moderation = 100
        organization = 100
        activity = 100
        community = 85
        bots_score = 100

        roles = list(guild.roles)
        channels = list(guild.channels)
        members = list(guild.members)
        bots = [m for m in members if m.bot]
        humans = [m for m in members if not m.bot]

        def add(severity, title, detail, recommendation):
            findings.append(Finding(severity, title, detail, recommendation))

        everyone = guild.default_role

        # Security
        if everyone.permissions.administrator:
            security -= 40
            add("critical", "@everyone has Administrator",
                "Every member may inherit unrestricted permissions.",
                "Remove Administrator from @everyone immediately.")

        broad = []
        for attr, label in [
            ("manage_guild", "Manage Server"),
            ("manage_roles", "Manage Roles"),
            ("manage_channels", "Manage Channels"),
            ("ban_members", "Ban Members"),
            ("kick_members", "Kick Members"),
            ("manage_webhooks", "Manage Webhooks"),
        ]:
            if getattr(everyone.permissions, attr, False):
                broad.append(label)

        if broad:
            security -= min(25, len(broad) * 5)
            add("high", "@everyone has powerful permissions",
                ", ".join(broad),
                "Move powerful permissions to trusted staff roles.")

        admin_roles = [
            r for r in roles
            if not r.managed and r != everyone and r.permissions.administrator
        ]
        if admin_roles:
            security -= min(20, len(admin_roles) * 5)
            add("high", f"{len(admin_roles)} Administrator role(s)",
                ", ".join(f"`{r.name}`" for r in admin_roles[:8]),
                "Review Administrator roles and apply least privilege.")

        admin_bots = [m for m in bots if m.guild_permissions.administrator]
        if admin_bots:
            security -= min(20, len(admin_bots) * 6)
            bots_score -= min(25, len(admin_bots) * 8)
            add("high", f"{len(admin_bots)} bot(s) have Administrator",
                ", ".join(f"`{m.display_name}`" for m in admin_bots[:8]),
                "Remove Administrator from bots unless absolutely required.")

        if guild.mfa_level == discord.MFALevel.disabled:
            security -= 7
            add("medium", "Moderator 2FA requirement is disabled",
                "The server does not require 2FA for moderation-level actions.",
                "Consider requiring 2FA for staff accounts.")

        if guild.verification_level < discord.VerificationLevel.medium:
            security -= 7
            add("medium", "Verification level is low",
                f"Current setting: {guild.verification_level.name.title()}.",
                "Increase verification if the server experiences spam or raids.")

        if guild.explicit_content_filter == discord.ContentFilter.disabled:
            security -= 4
            add("low", "Explicit content filtering is disabled",
                "Discord's explicit media filtering is not enabled.",
                "Consider enabling media content filtering.")

        # Role hierarchy
        powerful_roles = []
        for role in roles:
            if role.managed or role == everyone or role.permissions.administrator:
                continue
            perms = sum(bool(getattr(role.permissions, p)) for p in [
                "manage_guild", "manage_roles", "manage_channels",
                "ban_members", "kick_members", "manage_webhooks",
                "moderate_members", "manage_messages"
            ])
            if perms >= 4:
                powerful_roles.append(role)

        if powerful_roles:
            moderation -= min(18, len(powerful_roles) * 3)
            add("medium", "Broad moderation roles detected",
                ", ".join(f"`{r.name}`" for r in powerful_roles[:8]),
                "Split broad permissions between focused staff roles.")

        # Organization
        duplicates = {}
        for role in roles:
            if not role.managed:
                duplicates.setdefault(role.name.casefold(), []).append(role)
        duplicate_groups = [v for v in duplicates.values() if len(v) > 1]
        if duplicate_groups:
            organization -= min(12, len(duplicate_groups) * 3)
            add("low", "Duplicate role names",
                ", ".join(f"`{x[0].name}`" for x in duplicate_groups[:6]),
                "Rename duplicate roles to make responsibilities obvious.")

        empty_categories = [c for c in guild.categories if not c.channels]
        if empty_categories:
            organization -= min(10, len(empty_categories) * 2)
            add("low", "Empty categories detected",
                ", ".join(f"`{c.name}`" for c in empty_categories[:8]),
                "Archive or remove categories that are no longer useful.")

        uncategorized = [
            c for c in channels
            if not isinstance(c, discord.CategoryChannel) and c.category is None
        ]
        if len(uncategorized) >= 5:
            organization -= 7
            add("low", "Many uncategorized channels",
                f"{len(uncategorized)} channels are outside categories.",
                "Group related channels into categories.")

        # Channel permissions
        public_risky = []
        for channel in channels:
            overwrite = channel.overwrites_for(everyone)
            if overwrite.administrator or overwrite.manage_channels or overwrite.manage_roles:
                public_risky.append(channel)
        if public_risky:
            security -= min(15, len(public_risky) * 3)
            add("high", "Risky @everyone channel overwrites",
                ", ".join(f"`{c.name}`" for c in public_risky[:8]),
                "Review public channel overwrites and remove powerful permissions.")

        # Activity sample
        readable = [
            c for c in guild.text_channels
            if guild.me and c.permissions_for(guild.me).read_message_history
        ]
        sampled = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        for channel in readable[:60]:
            count = 0
            newest = None
            try:
                async for message in channel.history(limit=75):
                    count += 1
                    if newest is None:
                        newest = message.created_at.replace(tzinfo=timezone.utc)
            except (discord.Forbidden, discord.HTTPException):
                continue
            sampled.append((channel, count, newest))

        inactive = [
            item for item in sampled
            if item[2] is None or item[2] < cutoff
        ]

        if sampled and inactive:
            ratio = len(inactive) / len(sampled)
            activity -= min(25, int(ratio * 35))
            add("low" if ratio < .5 else "medium",
                f"{len(inactive)} sampled channel(s) appear inactive",
                "No recent messages were observed in the sampled history.",
                "Archive, repurpose, or review channels with consistently low activity.")

        if humans and len(bots) > max(5, len(humans) * 0.25):
            community -= 8
            bots_score -= 4
            add("low", "High bot-to-member ratio",
                f"{len(bots)} bots vs {len(humans)} cached human members.",
                "Review bots and integrations that are no longer needed.")

        # Webhooks
        try:
            webhooks = await guild.webhooks()
            if len(webhooks) > 25:
                bots_score -= 8
                add("medium", "Large webhook inventory",
                    f"{len(webhooks)} webhooks were found.",
                    "Review unused webhooks and delete stale integrations.")
        except (discord.Forbidden, discord.HTTPException):
            webhooks = []

        security = max(0, min(100, security))
        moderation = max(0, min(100, moderation))
        organization = max(0, min(100, organization))
        activity = max(0, min(100, activity))
        community = max(0, min(100, community))
        bots_score = max(0, min(100, bots_score))

        overall = round(
            security * .35
            + moderation * .15
            + organization * .15
            + activity * .15
            + community * .10
            + bots_score * .10
        )

        priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: priority.get(f.severity, 9))

        recommendations = []
        seen = set()
        for finding in findings:
            if finding.recommendation not in seen:
                recommendations.append(finding.recommendation)
                seen.add(finding.recommendation)

        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "overall": max(0, min(100, overall)),
            "security": security,
            "moderation": moderation,
            "organization": organization,
            "activity": activity,
            "community": community,
            "bots": bots_score,
            "findings": findings,
            "recommendations": recommendations[:8],
            "stats": {
                "members": guild.member_count or len(members),
                "humans": len(humans),
                "bots": len(bots),
                "roles": len(roles),
                "channels": len(channels),
                "categories": len(guild.categories),
                "text": len(guild.text_channels),
                "voice": len(guild.voice_channels),
                "forums": len(guild.forums),
                "webhooks": len(webhooks),
            },
        }
