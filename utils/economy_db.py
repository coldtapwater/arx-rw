from tortoise.exceptions import DoesNotExist
from utils.models.models import User, Inventory, Shop
import discord
from discord.ext import commands
import utils.configs as uc
from tortoise.functions import Sum
from tortoise.expressions import F



async def get_user_balance(user_id: int):
    user, _ = await User.get_or_create(id=user_id)
    return user.wallet, user.bank, user.gems

async def update_balance(user_id: int, wallet: int = 0, bank: int = 0, gems: int = 0):
    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        user = await User.create(id=user_id, wallet=0, bank=0, gems=0)
    
    user.wallet += wallet
    user.bank += bank
    user.gems += gems

    # Ensure balances don't go negative
    user.wallet = max(0, user.wallet)
    user.bank = max(0, user.bank)
    user.gems = max(0, user.gems)

    await user.save()
    return user.wallet, user.bank, user.gems


async def get_leaderboard(limit: int = 10):
    """
    Retrieve the leaderboard of users based on their total wealth.
    
    :param limit: Number of top users to retrieve (default: 10)
    :return: List of tuples containing (user_id, total_wealth)
    """
    leaderboard = await User.annotate(
        total_wealth=Sum(F('wallet') + F('bank') + F('gems'))
    ).order_by('-total_wealth').limit(limit).values('id', 'total_wealth')

    return [(entry['id'], entry['total_wealth']) for entry in leaderboard]

async def get_user_rank(user_id: int):
    """
    Get the rank of a specific user in the leaderboard.
    
    :param user_id: The ID of the user
    :return: The user's rank (1-based index) or None if user not found
    """
    user_wealth = await User.get(id=user_id).values('wallet', 'bank', 'gems')
    if not user_wealth:
        return None

    total_wealth = user_wealth['wallet'] + user_wealth['bank'] + user_wealth['gems']
    
    rank = await User.filter(
        (F('wallet') + F('bank') + F('gems')) > total_wealth
    ).count()

    return rank + 1  # Add 1 because ranks are 1-indexed

async def get_nearby_ranks(user_id: int, range: int = 2):
    """
    Get users ranked near the specified user.
    
    :param user_id: The ID of the user
    :param range: Number of users to retrieve above and below the specified user
    :return: List of tuples containing (user_id, total_wealth, rank)
    """
    user_rank = await get_user_rank(user_id)
    if user_rank is None:
        return []

    nearby_users = await User.annotate(
        total_wealth=Sum(F('wallet') + F('bank') + F('gems'))
    ).order_by('-total_wealth').offset(max(0, user_rank - range - 1)).limit(range * 2 + 1).values('id', 'total_wealth')

    return [(entry['id'], entry['total_wealth'], user_rank - range + i) 
            for i, entry in enumerate(nearby_users)]


async def add_item_to_inventory(user_id: int, item_name: str, quantity: int = 1):
    user, _ = await User.get_or_create(id=user_id)
    inventory_item, created = await Inventory.get_or_create(user=user, item_name=item_name)
    
    if created:
        inventory_item.quantity = quantity
    else:
        inventory_item.quantity += quantity
    
    await inventory_item.save()

async def get_user_inventory(user_id: int):
    user, _ = await User.get_or_create(id=user_id)
    inventory = await Inventory.filter(user=user).all()
    return inventory

async def get_shop_items():
    return await Shop.all()

async def add_items_to_shop(ctx, name: str, description: str, price: int, emoji: str, stackable: bool, sellable: bool):
    await Shop.create(name=name, description=description, price=price, emoji=emoji, sellable=stackable, stackable=stackable)
    return await ctx.send(f"{name} has been added to the shop!")

async def remove_items_from_shop(ctx, name: str):
    try:
        item = await Shop.get(name=name)
        await item.delete()
        return await ctx.send(f"{name} has been removed from the shop!")
    except DoesNotExist:
        return await ctx.send(f"{name} is not in the shop!")
    except Exception as e:
        return await ctx.send(f"An error occurred: {e}")
    
async def buy_item(ctx, name: str):
    try:
        item = await Shop.get(name=name)
        user = await User.get(id=ctx.author.id)
        if user.wallet < item.price:
            return await ctx.send(f"You don't have enough money to buy {name}!")
        
        user.wallet -= item.price
        await user.save()
        
        try:
            await add_item_to_inventory(ctx.author.id, name, 1)
        except Exception as e:
            # If adding to inventory fails, refund the user
            user.wallet += item.price
            await user.save()
            raise Exception(f"Failed to add item to inventory: {str(e)}")
        
        return await ctx.send(f"You have successfully purchased {name}!")
    except DoesNotExist:
        return await ctx.send(f"{name} is not in the shop!")
    except Exception as e:
        return await ctx.send(f"An error occurred: {e}")

async def sell_item(ctx, name: str):
    try:
        item = await Shop.get(name=name)
        user = await User.get(id=ctx.author.id)
        inventory_item = await Inventory.get(user=user, item_name=name)
        if inventory_item.quantity == 0:
            return await ctx.send(f"You don't have any {name} to sell!")
        inventory_item.quantity -= 1
        await inventory_item.save()
        user.wallet += item.price
        await user.save()
        return await ctx.send(f"You have successfully sold {name}!")
    except DoesNotExist:
        return await ctx.send(f"{name} is not in the shop!")
    except Exception as e:
        return await ctx.send(f"An error occurred: {e}")
    

async def get_total_buckaroos():
    users = await User.all()
    return sum(user.wallet + user.bank for user in users)

# Add these imports at the top of the file
from tortoise.exceptions import DoesNotExist

# Add these new functions

async def remove_item_from_inventory(user_id: int, item_name: str, quantity: int = 1):
    user = await User.get(id=user_id)
    try:
        inventory_item = await Inventory.get(user=user, item_name=item_name)
        if inventory_item.quantity >= quantity:
            inventory_item.quantity -= quantity
            if inventory_item.quantity == 0:
                await inventory_item.delete()
            else:
                await inventory_item.save()
        else:
            raise ValueError("Not enough items in inventory")
    except DoesNotExist:
        raise ValueError("Item not found in inventory")

async def add_badge(user_id: int, badge_name: str):
    user = await User.get(id=user_id)
    badge, created = await Badge.get_or_create(user=user, name=badge_name)
    if not created:
        badge.count += 1
        await badge.save()

async def get_user_badges(user_id: int):
    user = await User.get(id=user_id)
    return await Badge.filter(user=user).all()