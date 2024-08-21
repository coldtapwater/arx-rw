import aiosqlite
import os



async def init_db():
    async with aiosqlite.connect('bot.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            wallet INTEGER NOT NULL,
            bank INTEGER NOT NULL,
            gems INTEGER NOT NULL
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            PRIMARY KEY (user_id, item_name)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS shop (
            name TEXT PRIMARY KEY,
            price INTEGER NOT NULL,
            description TEXT NOT NULL,
            emoji TEXT NOT NULL,
            sellable BOOLEAN NOT NULL,
            stackable BOOLEAN NOT NULL
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS investments (
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            period TEXT NOT NULL,
            end_date TEXT NOT NULL,
            PRIMARY KEY (user_id, name)
        )''')
        await db.commit()

# Functions to interact with the database
async def get_user_data(user_id):
    async with aiosqlite.connect('bot.db') as db:
        async with db.execute('SELECT wallet, bank, gems FROM users WHERE id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result is None:
                # User doesn't exist, create a new entry
                await db.execute('INSERT INTO users (id, wallet, bank, gems) VALUES (?, ?, ?, ?)', (user_id, 0, 0, 0))
                await db.commit()
                result = (0, 0, 0)
            return result

async def get_custom_users(user_id):
    async with aiosqlite.connect('bot.db') as db:
        async with db.execute('SELECT * FROM custom_profiles WHERE id = ?', (user_id,)) as cursor:
            return await cursor.fetchall()

async def create_user(user_id):
    async with aiosqlite.connect('bot.db') as db:
        await db.execute('INSERT INTO users (id, wallet, bank, gems) VALUES (?, ?, ?, ?)', (user_id, 0, 0, 0))
        await db.commit()

async def save_user_data(user_id, wallet, bank, gems):
    async with aiosqlite.connect('bot.db') as db:
        await db.execute('UPDATE users SET wallet = ?, bank = ?, gems = ? WHERE id = ?', (wallet, bank, gems, user_id))
        await db.commit()

async def get_inventory(user_id):
    async with aiosqlite.connect('bot.db') as db:
        async with db.execute('SELECT item_name, quantity, weapon FROM inventory WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchall()
        
async def get_upgrades_inventory(user_id):
    upgrades_inventory = {}
    async with aiosqlite.connect('bot.db') as db:
        async with db.execute('SELECT item_name, tag FROM upgrades_inventory WHERE user_id = ?', (user_id,)) as cursor:
            async for row in cursor:
                item_name = row[0]
                if item_name in upgrades_inventory:
                    upgrades_inventory[item_name] += 1
                else:
                    upgrades_inventory[item_name] = 1
    return upgrades_inventory


async def save_inventory(user_id, item_name, quantity, weapon=False):
    async with aiosqlite.connect('bot.db') as db:
        # Check if the item already exists in the inventory
        async with db.execute('SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, item_name)) as cursor:
            result = await cursor.fetchone()
        if result:
            # Update the quantity if the item exists
            await db.execute('UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_name = ? AND weapon = ?', (quantity, user_id, item_name, weapon))
        else:
            # Insert a new item if it does not exist
            await db.execute('INSERT INTO inventory (user_id, item_name, quantity, weapon) VALUES (?, ?, ?, ?)', (user_id, item_name, quantity, weapon))
        await db.commit()

async def get_shop_items():
    async with aiosqlite.connect('bot.db') as db:
        async with db.execute('SELECT name, price, description, emoji, sellable, stackable FROM shop') as cursor:
            return await cursor.fetchall()

async def add_shop_item(name, price, description, emoji, sellable, stackable):
    async with aiosqlite.connect('bot.db') as db:
        await db.execute('REPLACE INTO shop (name, price, description, emoji, sellable, stackable) VALUES (?, ?, ?, ?, ?, ?)', 
                         (name, price, description, emoji, sellable, stackable))
        await db.commit()

async def give_item(user_id, member_id, item):
    async with aiosqlite.connect('bot.db') as db:
        async with db.execute('SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, item)) as cursor:
            result = await cursor.fetchone()
        if result:
            await db.execute('UPDATE inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_name = ?', (member_id, item))
        else:
            await db.execute('INSERT INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 1)', (member_id, item))
        await db.commit()