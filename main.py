import discord
from discord.ext import commands
import os
import sqlite3
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "profiles.db"


def db():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            discord_id TEXT PRIMARY KEY,
            uid TEXT,
            nickname TEXT,
            region TEXT,
            level INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            br_rank TEXT,
            cs_rank TEXT,
            guild_name TEXT,
            guild_id TEXT,
            bio TEXT,
            pet TEXT,
            character_name TEXT,
            evo_gun TEXT,
            badges TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def upsert_profile(discord_id, field_values):
    conn = db()
    cur = conn.cursor()

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("SELECT discord_id FROM profiles WHERE discord_id = ?", (str(discord_id),))
    exists = cur.fetchone()

    if exists:
        sets = ", ".join([f"{key} = ?" for key in field_values.keys()])
        values = list(field_values.values()) + [now, str(discord_id)]
        cur.execute(
            f"UPDATE profiles SET {sets}, updated_at = ? WHERE discord_id = ?",
            values
        )
    else:
        data = {
            "uid": None,
            "nickname": None,
            "region": None,
            "level": 0,
            "likes": 0,
            "br_rank": None,
            "cs_rank": None,
            "guild_name": None,
            "guild_id": None,
            "bio": None,
            "pet": None,
            "character_name": None,
            "evo_gun": None,
            "badges": None,
            "created_at": now,
            "updated_at": now
        }
        data.update(field_values)

        cur.execute("""
            INSERT INTO profiles (
                discord_id, uid, nickname, region, level, likes,
                br_rank, cs_rank, guild_name, guild_id, bio, pet,
                character_name, evo_gun, badges, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(discord_id),
            data["uid"],
            data["nickname"],
            data["region"],
            data["level"],
            data["likes"],
            data["br_rank"],
            data["cs_rank"],
            data["guild_name"],
            data["guild_id"],
            data["bio"],
            data["pet"],
            data["character_name"],
            data["evo_gun"],
            data["badges"],
            data["created_at"],
            data["updated_at"]
        ))

    conn.commit()
    conn.close()


def get_profile(discord_id):
    conn = db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM profiles WHERE discord_id = ?", (str(discord_id),))
    row = cur.fetchone()
    conn.close()
    return row


def get_profile_by_member(member_id):
    return get_profile(member_id)


@bot.event
async def on_ready():
    init_db()
    print(f"Bot pornit ca {bot.user}")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def setuid(ctx, uid: str):
    upsert_profile(ctx.author.id, {"uid": uid})
    await ctx.send(f"UID salvat pentru {ctx.author.mention}: `{uid}`")


@bot.command()
async def editprofil(
    ctx,
    field: str,
    *,
    value: str
):
    allowed_fields = {
        "uid": "uid",
        "nickname": "nickname",
        "region": "region",
        "level": "level",
        "likes": "likes",
        "br_rank": "br_rank",
        "cs_rank": "cs_rank",
        "guild_name": "guild_name",
        "guild_id": "guild_id",
        "bio": "bio",
        "pet": "pet",
        "character": "character_name",
        "character_name": "character_name",
        "evo_gun": "evo_gun",
        "badges": "badges"
    }

    if field not in allowed_fields:
        await ctx.send(
            "Câmp invalid. Folosește unul dintre: "
            "`uid, nickname, region, level, likes, br_rank, cs_rank, guild_name, guild_id, bio, pet, character, evo_gun, badges`"
        )
        return

    db_field = allowed_fields[field]

    if db_field in ["level", "likes"]:
        try:
            value = int(value)
        except ValueError:
            await ctx.send("Pentru `level` și `likes` trebuie să pui un număr.")
            return

    upsert_profile(ctx.author.id, {db_field: value})
    await ctx.send(f"Am actualizat `{db_field}` pentru {ctx.author.mention}.")


@bot.command()
async def profil(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat pentru acest utilizator.")
        return

    embed = discord.Embed(
        title=f"Profil Free Fire - {member.display_name}",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="UID", value=profile["uid"] or "Nesetat", inline=True)
    embed.add_field(name="Nickname", value=profile["nickname"] or "Nesetat", inline=True)
    embed.add_field(name="Region", value=profile["region"] or "Nesetat", inline=True)

    embed.add_field(name="Level", value=profile["level"] if profile["level"] is not None else 0, inline=True)
    embed.add_field(name="Likes", value=profile["likes"] if profile["likes"] is not None else 0, inline=True)
    embed.add_field(name="Pet", value=profile["pet"] or "Nesetat", inline=True)

    embed.add_field(name="BR Rank", value=profile["br_rank"] or "Nesetat", inline=True)
    embed.add_field(name="CS Rank", value=profile["cs_rank"] or "Nesetat", inline=True)
    embed.add_field(name="Character", value=profile["character_name"] or "Nesetat", inline=True)

    embed.add_field(name="Guild Name", value=profile["guild_name"] or "Nesetat", inline=True)
    embed.add_field(name="Guild ID", value=profile["guild_id"] or "Nesetat", inline=True)
    embed.add_field(name="Evo Gun", value=profile["evo_gun"] or "Nesetat", inline=True)

    embed.add_field(name="Badges", value=profile["badges"] or "Nesetat", inline=False)
    embed.add_field(name="Bio", value=profile["bio"] or "Nesetat", inline=False)

    embed.set_footer(
        text=f"Creat: {profile['created_at'] or '-'} | Update: {profile['updated_at'] or '-'}"
    )

    await ctx.send(embed=embed)


@bot.command()
async def likes(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat.")
        return

    await ctx.send(f"{member.mention} are **{profile['likes'] or 0}** likes.")


@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat.")
        return

    await ctx.send(
        f"{member.mention} | BR Rank: **{profile['br_rank'] or 'Nesetat'}** | "
        f"CS Rank: **{profile['cs_rank'] or 'Nesetat'}**"
    )


@bot.command()
async def guild(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat.")
        return

    await ctx.send(
        f"{member.mention} | Guild: **{profile['guild_name'] or 'Nesetat'}** "
        f"(ID: `{profile['guild_id'] or 'Nesetat'}`)"
    )


@bot.command()
async def top(ctx):
    conn = db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT discord_id, nickname, likes, level
        FROM profiles
        ORDER BY likes DESC, level DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await ctx.send("Nu există profiluri salvate.")
        return

    text = "**Top profiluri după likes:**\n"
    for i, row in enumerate(rows, start=1):
        member = ctx.guild.get_member(int(row["discord_id"]))
        display_name = row["nickname"] or (member.display_name if member else row["discord_id"])
        text += f"{i}. {display_name} — {row['likes'] or 0} likes | lvl {row['level'] or 0}\n"

    await ctx.send(text)


@bot.command()
@commands.has_permissions(administrator=True)
async def deleteprofil(ctx, member: discord.Member):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM profiles WHERE discord_id = ?", (str(member.id),))
    conn.commit()
    conn.close()
    await ctx.send(f"Profilul lui {member.mention} a fost șters.")


@deleteprofil.error
async def deleteprofil_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nu ai permisiune pentru această comandă.")


bot.run(os.getenv("TOKEN"))
from discord.ext import commands
import os
import sqlite3
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "profiles.db"


def db():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            discord_id TEXT PRIMARY KEY,
            uid TEXT,
            nickname TEXT,
            region TEXT,
            level INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            br_rank TEXT,
            cs_rank TEXT,
            guild_name TEXT,
            guild_id TEXT,
            bio TEXT,
            pet TEXT,
            character_name TEXT,
            evo_gun TEXT,
            badges TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def upsert_profile(discord_id, field_values):
    conn = db()
    cur = conn.cursor()

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("SELECT discord_id FROM profiles WHERE discord_id = ?", (str(discord_id),))
    exists = cur.fetchone()

    if exists:
        sets = ", ".join([f"{key} = ?" for key in field_values.keys()])
        values = list(field_values.values()) + [now, str(discord_id)]
        cur.execute(
            f"UPDATE profiles SET {sets}, updated_at = ? WHERE discord_id = ?",
            values
        )
    else:
        data = {
            "uid": None,
            "nickname": None,
            "region": None,
            "level": 0,
            "likes": 0,
            "br_rank": None,
            "cs_rank": None,
            "guild_name": None,
            "guild_id": None,
            "bio": None,
            "pet": None,
            "character_name": None,
            "evo_gun": None,
            "badges": None,
            "created_at": now,
            "updated_at": now
        }
        data.update(field_values)

        cur.execute("""
            INSERT INTO profiles (
                discord_id, uid, nickname, region, level, likes,
                br_rank, cs_rank, guild_name, guild_id, bio, pet,
                character_name, evo_gun, badges, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(discord_id),
            data["uid"],
            data["nickname"],
            data["region"],
            data["level"],
            data["likes"],
            data["br_rank"],
            data["cs_rank"],
            data["guild_name"],
            data["guild_id"],
            data["bio"],
            data["pet"],
            data["character_name"],
            data["evo_gun"],
            data["badges"],
            data["created_at"],
            data["updated_at"]
        ))

    conn.commit()
    conn.close()


def get_profile(discord_id):
    conn = db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM profiles WHERE discord_id = ?", (str(discord_id),))
    row = cur.fetchone()
    conn.close()
    return row


def get_profile_by_member(member_id):
    return get_profile(member_id)


@bot.event
async def on_ready():
    init_db()
    print(f"Bot pornit ca {bot.user}")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def setuid(ctx, uid: str):
    upsert_profile(ctx.author.id, {"uid": uid})
    await ctx.send(f"UID salvat pentru {ctx.author.mention}: `{uid}`")


@bot.command()
async def editprofil(
    ctx,
    field: str,
    *,
    value: str
):
    allowed_fields = {
        "uid": "uid",
        "nickname": "nickname",
        "region": "region",
        "level": "level",
        "likes": "likes",
        "br_rank": "br_rank",
        "cs_rank": "cs_rank",
        "guild_name": "guild_name",
        "guild_id": "guild_id",
        "bio": "bio",
        "pet": "pet",
        "character": "character_name",
        "character_name": "character_name",
        "evo_gun": "evo_gun",
        "badges": "badges"
    }

    if field not in allowed_fields:
        await ctx.send(
            "Câmp invalid. Folosește unul dintre: "
            "`uid, nickname, region, level, likes, br_rank, cs_rank, guild_name, guild_id, bio, pet, character, evo_gun, badges`"
        )
        return

    db_field = allowed_fields[field]

    if db_field in ["level", "likes"]:
        try:
            value = int(value)
        except ValueError:
            await ctx.send("Pentru `level` și `likes` trebuie să pui un număr.")
            return

    upsert_profile(ctx.author.id, {db_field: value})
    await ctx.send(f"Am actualizat `{db_field}` pentru {ctx.author.mention}.")


@bot.command()
async def profil(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat pentru acest utilizator.")
        return

    embed = discord.Embed(
        title=f"Profil Free Fire - {member.display_name}",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="UID", value=profile["uid"] or "Nesetat", inline=True)
    embed.add_field(name="Nickname", value=profile["nickname"] or "Nesetat", inline=True)
    embed.add_field(name="Region", value=profile["region"] or "Nesetat", inline=True)

    embed.add_field(name="Level", value=profile["level"] if profile["level"] is not None else 0, inline=True)
    embed.add_field(name="Likes", value=profile["likes"] if profile["likes"] is not None else 0, inline=True)
    embed.add_field(name="Pet", value=profile["pet"] or "Nesetat", inline=True)

    embed.add_field(name="BR Rank", value=profile["br_rank"] or "Nesetat", inline=True)
    embed.add_field(name="CS Rank", value=profile["cs_rank"] or "Nesetat", inline=True)
    embed.add_field(name="Character", value=profile["character_name"] or "Nesetat", inline=True)

    embed.add_field(name="Guild Name", value=profile["guild_name"] or "Nesetat", inline=True)
    embed.add_field(name="Guild ID", value=profile["guild_id"] or "Nesetat", inline=True)
    embed.add_field(name="Evo Gun", value=profile["evo_gun"] or "Nesetat", inline=True)

    embed.add_field(name="Badges", value=profile["badges"] or "Nesetat", inline=False)
    embed.add_field(name="Bio", value=profile["bio"] or "Nesetat", inline=False)

    embed.set_footer(
        text=f"Creat: {profile['created_at'] or '-'} | Update: {profile['updated_at'] or '-'}"
    )

    await ctx.send(embed=embed)


@bot.command()
async def likes(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat.")
        return

    await ctx.send(f"{member.mention} are **{profile['likes'] or 0}** likes.")


@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat.")
        return

    await ctx.send(
        f"{member.mention} | BR Rank: **{profile['br_rank'] or 'Nesetat'}** | "
        f"CS Rank: **{profile['cs_rank'] or 'Nesetat'}**"
    )


@bot.command()
async def guild(ctx, member: discord.Member = None):
    member = member or ctx.author
    profile = get_profile_by_member(member.id)

    if not profile:
        await ctx.send("Nu există profil salvat.")
        return

    await ctx.send(
        f"{member.mention} | Guild: **{profile['guild_name'] or 'Nesetat'}** "
        f"(ID: `{profile['guild_id'] or 'Nesetat'}`)"
    )


@bot.command()
async def top(ctx):
    conn = db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT discord_id, nickname, likes, level
        FROM profiles
        ORDER BY likes DESC, level DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await ctx.send("Nu există profiluri salvate.")
        return

    text = "**Top profiluri după likes:**\n"
    for i, row in enumerate(rows, start=1):
        member = ctx.guild.get_member(int(row["discord_id"]))
        display_name = row["nickname"] or (member.display_name if member else row["discord_id"])
        text += f"{i}. {display_name} — {row['likes'] or 0} likes | lvl {row['level'] or 0}\n"

    await ctx.send(text)


@bot.command()
@commands.has_permissions(administrator=True)
async def deleteprofil(ctx, member: discord.Member):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM profiles WHERE discord_id = ?", (str(member.id),))
    conn.commit()
    conn.close()
    await ctx.send(f"Profilul lui {member.mention} a fost șters.")


@deleteprofil.error
async def deleteprofil_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nu ai permisiune pentru această comandă.")


bot.run(os.getenv("TOKEN"))
