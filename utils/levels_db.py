from tortoise.exceptions import DoesNotExist
from utils.models.models import UserLevel, User
import math
import time
import utils.economy_db as economy_db

async def get_user_level(user_id: int, guild_id: int):
    user_level, _ = await UserLevel.get_or_create(user_id=user_id, guild_id=guild_id)
    return user_level

async def update_user_xp(user_id: int, guild_id: int, xp_gain: int):
    user_level = await get_user_level(user_id, guild_id)
    
    current_time = int(time.time())
    if current_time - user_level.last_xp_gain < 60:  # 60 seconds cooldown
        return user_level.xp, user_level.level, False

    user_level.xp += xp_gain
    user_level.last_xp_gain = current_time

    new_level = calculate_level(user_level.xp)
    leveled_up = new_level > user_level.level
    user_level.level = new_level

    await user_level.save()
    return user_level.xp, user_level.level, leveled_up

def calculate_level(xp: int) -> int:
    return int((xp / 100) ** 0.5)

def calculate_xp_for_next_level(level: int) -> int:
    return (level + 1) ** 2 * 100

async def get_leaderboard(guild_id: int, limit: int = 10):
    leaderboard = await UserLevel.filter(guild_id=guild_id).order_by('-xp').limit(limit)
    return [(user_level.user_id, user_level.xp, user_level.level) for user_level in leaderboard]

async def add_prestige(user_id: int, guild_id: int):
    user_level = await get_user_level(user_id, guild_id)
    
    if user_level.level >= 100:
        user_level.prestige += 1
        user_level.xp = 0
        user_level.level = 0
        await economy_db.update_balance(user_id, wallet=25000)
        await user_level.save()
        return True
    return False

async def calculate_xp_gain(message_content: str, is_booster: bool):
    word_count = len(message_content.split())
    xp = int(word_count * 0.5)  # Base XP calculation
    if is_booster:
        xp = int(xp * 1.5)  # 50% bonus for boosters
    return min(xp, 50)  # Cap at 50 XP per message

async def get_level_up_bonus(level: int) -> int:
    return int(10 * (1.1 ** level)) 