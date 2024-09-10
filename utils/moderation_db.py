from tortoise.exceptions import DoesNotExist
from utils.models.models import GuildConfig, ModLog, LogAction

async def get_guild_config(guild_id: int):
    config, _ = await GuildConfig.get_or_create(guild_id=guild_id)
    return config

async def update_guild_config(guild_id: int, **kwargs):
    config, _ = await GuildConfig.get_or_create(guild_id=guild_id)
    for key, value in kwargs.items():
        setattr(config, key, value)
    await config.save()

async def add_mod_log(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str = None):
    await ModLog.create(
        guild_id=guild_id,
        user_id=user_id,
        moderator_id=moderator_id,
        action=action,
        reason=reason
    )

async def get_mod_logs(guild_id: int, user_id: int = None):
    query = ModLog.filter(guild_id=guild_id)
    if user_id:
        query = query.filter(user_id=user_id)
    return await query.order_by('-timestamp').all()

async def add_log_action(guild_id: int, action_type: str, details: str):
    await LogAction.create(
        guild_id=guild_id,
        action_type=action_type,
        details=details
    )

# Add more moderation-related database functions here