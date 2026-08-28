import discord
from datetime import datetime

def bar(score, size=12):
    filled = round(score / 100 * size)
    return "█" * filled + "░" * (size - filled)

def severity_icon(value):
    return {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
    }.get(value, "ℹ️")

def label(score):
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Good"
    if score >= 70:
        return "Fair"
    if score >= 50:
        return "Needs Attention"
    return "Critical"

def base(guild, title, description=None):
    embed = discord.Embed(
        title=title,
        description=description,
        timestamp=datetime.now().astimezone(),
    )
    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    else:
        embed.set_author(name=guild.name)
    embed.set_footer(text="Server Health • Read-only audit")
    return embed

def report_embed(guild, report):
    embed = base(
        guild,
        "🏥 Advanced Server Health Report",
        f"## {report['overall']}/100 — {label(report['overall'])}\n"
        f"`{bar(report['overall'], 20)}`"
    )

    for key, name, icon in [
        ("security", "Security", "🛡️"),
        ("moderation", "Moderation", "🔨"),
        ("organization", "Organization", "📁"),
        ("activity", "Activity", "📊"),
        ("community", "Community", "👥"),
        ("bots", "Bots / Integrations", "🤖"),
    ]:
        score = report[key]
        embed.add_field(
            name=f"{icon} {name}",
            value=f"**{score}/100**\n`{bar(score)}`",
            inline=True,
        )

    s = report["stats"]
    embed.add_field(
        name="📈 Server Statistics",
        value=(
            f"Members: **{s['members']:,}**\n"
            f"Humans: **{s['humans']:,}**\n"
            f"Bots: **{s['bots']:,}**\n"
            f"Roles: **{s['roles']:,}**\n"
            f"Channels: **{s['channels']:,}**\n"
            f"Webhooks: **{s['webhooks']:,}**"
        ),
        inline=True,
    )

    findings = report["findings"][:7]
    if findings:
        text = "\n\n".join(
            f"{severity_icon(f.severity)} **{f.title}**\n{f.detail}"
            for f in findings
        )
        embed.add_field(name="🔎 Key Findings", value=text[:1024], inline=False)
    else:
        embed.add_field(
            name="✅ No major findings",
            value="The audit did not identify the configured risk patterns.",
            inline=False,
        )

    if report["recommendations"]:
        text = "\n".join(
            f"**{i}.** {x}"
            for i, x in enumerate(report["recommendations"], 1)
        )
        embed.add_field(name="💡 Recommendations", value=text[:1024], inline=False)

    return embed

def findings_embed(guild, title, findings):
    embed = base(guild, title)
    if not findings:
        embed.description = "✅ No findings in this category."
        return embed
    for f in findings[:12]:
        embed.add_field(
            name=f"{severity_icon(f.severity)} {f.title}",
            value=f"{f.detail}\n**Recommendation:** {f.recommendation}",
            inline=False,
        )
    return embed

def history_embed(guild, rows):
    embed = base(guild, "📈 Health History")
    if not rows:
        embed.description = "No historical reports have been saved yet."
        return embed

    lines = []
    for row in rows:
        created, overall, security, moderation, organization, activity, community, bots, findings = row
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            date = dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            date = created
        lines.append(
            f"**{date}** — **{overall}/100** "
            f"(🛡 {security} • 🔨 {moderation} • 📁 {organization} • "
            f"📊 {activity} • 👥 {community} • 🤖 {bots}) — "
            f"{findings} finding(s)"
        )

    embed.description = "\n".join(lines)[:4096]
    return embed
