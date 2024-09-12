from tortoise.functions import Count
from utils.models.models import User, GuildConfig, Supporters
import time
async def get_total_users():
    return await User.all().count()

async def get_top_users(limit: int = 10):
    return await User.all().order_by('-wallet').limit(limit)

async def get_user_rank(user_id: int):
    user = await User.get(id=user_id)
    rank = await User.filter(wallet__gt=user.wallet).count()
    return rank + 1

async def get_all_guild_configs():
    return await GuildConfig.all()

async def search_users(query: str):
    # This assumes you have a username field in your User model
    return await User.filter(username__icontains=query).all()



async def get_supporters():
    return await Supporters.all()

async def add_supporter(user_id: int):
    await Supporters.create(user_id=user_id)    
# Add more general/misc database functions here