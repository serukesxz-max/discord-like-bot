import os
import requests
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

FF_API_KEY = os.getenv("FF_API_KEY")
FF_USER_UID = os.getenv("FF_USER_UID")
FF_REGION = os.getenv("FF_REGION", "sg")

ACCOUNT_ENDPOINT = "https://proapis.hlgamingofficial.com/main/games/freefire/account/api"

def ff_account_lookup(player_uid: str, region: str | None = None) -> dict:
    region = region or FF_REGION

    if not FF_API_KEY or not FF_USER_UID:
        raise RuntimeError("Lipsesc FF_API_KEY sau FF_USER_UID din variabilele Railway.")

    params = {
        "sectionName": "AllData",
        "PlayerUid": str(player_uid),
        "region": region,
        "useruid": FF_USER_UID,
        "api": FF_API_KEY,
    }

    response = requests.get(ACCOUNT_ENDPOINT, params=params, timeout=25)
    response.raise_for_status()
    return response.json()

def safe_get(dct, *keys, default="Nesetat"):
    cur = dct
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur if cur not in (None, "", []) else default

@bot.event
async def on_ready():
    print(f"Bot pornit ca {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def profil(ctx, uid: str, region: str | None = None):
    try:
        data = ff_account_lookup(uid, region)
    except requests.HTTPError as e:
        await ctx.send(f"Eroare HTTP la API: {e}")
        return
    except requests.RequestException as e:
        await ctx.send(f"Eroare de rețea: {e}")
        return
    except Exception as e:
        await ctx.send(f"Eroare: {e}")
        return

    result = data.get("result", {})
    account = result.get("AccountInfo", {})
    profile = result.get("AccountProfileInfo", {})
    guild = result.get("GuildInfo", {})
    pet = result.get("petInfo", {}) or result.get("PetInfo", {})

    name = safe_get(account, "AccountName")
    region_value = safe_get(account, "AccountRegion")
    level = safe_get(account, "AccountLevel", default=0)
    likes = safe_get(account, "AccountLikes", default=0)
    br_points = safe_get(account, "BrRankPoint", default=0)
    cs_points = safe_get(account, "CsRankPoint", default=0)

    bio = safe_get(profile, "AccountSignature")
    outfit = safe_get(profile, "EquippedOutfit", default=[])
    outfit_count = len(outfit) if isinstance(outfit, list) else 0

    guild_name = safe_get(guild, "GuildName")
    guild_id = safe_get(guild, "GuildID")
    pet_name = safe_get(pet, "equippedPetName")

    embed = discord.Embed(
        title=f"Free Fire Profile: {name}",
        description=f"UID: `{uid}`",
        color=discord.Color.orange()
    )

    embed.add_field(name="Region", value=str(region_value), inline=True)
    embed.add_field(name="Level", value=str(level), inline=True)
    embed.add_field(name="Likes", value=str(likes), inline=True)

    embed.add_field(name="BR Rank Points", value=str(br_points), inline=True)
    embed.add_field(name="CS Rank Points", value=str(cs_points), inline=True)
    embed.add_field(name="Pet", value=str(pet_name), inline=True)

    embed.add_field(name="Guild Name", value=str(guild_name), inline=True)
    embed.add_field(name="Guild ID", value=str(guild_id), inline=True)
    embed.add_field(name="Outfit Items", value=str(outfit_count), inline=True)

    embed.add_field(name="Bio", value=str(bio), inline=False)

    source_name = data.get("source", "HL Gaming Official")
    endpoint_name = data.get("endpoint", "AllData")
    embed.set_footer(text=f"Source: {source_name} | Endpoint: {endpoint_name}")

    await ctx.send(embed=embed)

@bot.command()
async def validuid(ctx, uid: str, region: str | None = None):
    region = region or FF_REGION

    if not FF_API_KEY or not FF_USER_UID:
        await ctx.send("Lipsesc FF_API_KEY sau FF_USER_UID în Railway.")
        return

    params = {
        "sectionName": "freefireValidation",
        "uid": str(uid),
        "region": region,
        "useruid": FF_USER_UID,
        "api": FF_API_KEY,
    }

    try:
        response = requests.get(ACCOUNT_ENDPOINT, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        await ctx.send(f"Eroare la validare UID: {e}")
        return

    await ctx.send(f"Răspuns validare UID pentru `{uid}`:\n```json\n{str(data)[:1800]}\n```")

bot.run(os.getenv("TOKEN"))
