from pathlib import Path
import aiosqlite

class Database:
    def __init__(self, path: str):
        self.path = path
        self.connection = None

    async def initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.path)
        await self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS health_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            overall INTEGER NOT NULL,
            security INTEGER NOT NULL,
            moderation INTEGER NOT NULL,
            organization INTEGER NOT NULL,
            activity INTEGER NOT NULL,
            community INTEGER NOT NULL,
            bots INTEGER NOT NULL,
            findings INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id INTEGER PRIMARY KEY,
            report_channel_id INTEGER,
            alerts_enabled INTEGER NOT NULL DEFAULT 1,
            schedule_enabled INTEGER NOT NULL DEFAULT 0,
            schedule_hour INTEGER NOT NULL DEFAULT 9,
            schedule_minute INTEGER NOT NULL DEFAULT 0
        );
        """)
        await self.connection.commit()

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def save_report(self, guild_id, report):
        await self.connection.execute(
            """INSERT INTO health_reports
            (guild_id, created_at, overall, security, moderation,
             organization, activity, community, bots, findings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                guild_id, report["created_at"], report["overall"],
                report["security"], report["moderation"],
                report["organization"], report["activity"],
                report["community"], report["bots"],
                len(report["findings"]),
            ),
        )
        await self.connection.commit()

    async def history(self, guild_id, limit=10):
        cursor = await self.connection.execute(
            """SELECT created_at, overall, security, moderation,
               organization, activity, community, bots, findings
               FROM health_reports
               WHERE guild_id = ?
               ORDER BY id DESC LIMIT ?""",
            (guild_id, limit),
        )
        return await cursor.fetchall()

    async def get_config(self, guild_id):
        cursor = await self.connection.execute(
            "SELECT guild_id, report_channel_id, alerts_enabled, schedule_enabled, schedule_hour, schedule_minute FROM guild_config WHERE guild_id=?",
            (guild_id,),
        )
        row = await cursor.fetchone()
        if row:
            return row
        await self.connection.execute(
            "INSERT INTO guild_config (guild_id) VALUES (?)", (guild_id,)
        )
        await self.connection.commit()
        return (guild_id, None, 1, 0, 9, 0)

    async def set_channel(self, guild_id, channel_id):
        await self.get_config(guild_id)
        await self.connection.execute(
            "UPDATE guild_config SET report_channel_id=? WHERE guild_id=?",
            (channel_id, guild_id),
        )
        await self.connection.commit()

    async def set_alerts(self, guild_id, enabled):
        await self.get_config(guild_id)
        await self.connection.execute(
            "UPDATE guild_config SET alerts_enabled=? WHERE guild_id=?",
            (1 if enabled else 0, guild_id),
        )
        await self.connection.commit()

    async def set_schedule(self, guild_id, enabled, hour, minute):
        await self.get_config(guild_id)
        await self.connection.execute(
            "UPDATE guild_config SET schedule_enabled=?, schedule_hour=?, schedule_minute=? WHERE guild_id=?",
            (1 if enabled else 0, hour, minute, guild_id),
        )
        await self.connection.commit()
