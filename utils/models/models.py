from tortoise import fields
from tortoise.models import Model

class UnoGame(Model):
    channel_id = fields.BigIntField(pk=True)
    game_data = fields.TextField()

    class Meta:
        table = "games"

class User(Model):
    id = fields.BigIntField(pk=True)
    wallet = fields.IntField(default=0)
    bank = fields.IntField(default=0)
    gems = fields.IntField(default=0)

    class Meta:
        table = "users"

class Inventory(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='inventory_items')
    item_name = fields.CharField(max_length=255)
    quantity = fields.IntField()

    class Meta:
        table = "inventory"
        unique_together = ("user", "item_name")

class Shop(Model):
    name = fields.CharField(max_length=255, pk=True)
    price = fields.IntField()
    description = fields.TextField()
    emoji = fields.CharField(max_length=255)
    sellable = fields.BooleanField()
    stackable = fields.BooleanField()

    class Meta:
        table = "shop"

class GuildConfig(Model):
    guild_id = fields.BigIntField(pk=True)
    prefix = fields.CharField(max_length=10, default='!')
    mod_role_id = fields.BigIntField(null=True)
    mute_role_id = fields.BigIntField(null=True)
    log_channel_id = fields.BigIntField(null=True)

    class Meta:
        table = "guild_configs"

class ModLog(Model):
    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    user_id = fields.BigIntField()
    moderator_id = fields.BigIntField()
    action = fields.CharField(max_length=20)
    reason = fields.TextField(null=True)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "mod_logs"

class LogAction(Model):
    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    action_type = fields.CharField(max_length=50)
    details = fields.TextField()
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "log_actions"

class BlacklistedUser(Model):
    user_id = fields.BigIntField(pk=True)
    reason = fields.TextField()
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "blacklisted_users"

class AuditedUser(Model):
    user_id = fields.BigIntField(pk=True)
    reason = fields.TextField()
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audited_users"

class Supporters(Model):
    user_id = fields.BigIntField(pk=True)

    class Meta:
        table = "supporters"

class UserLevel(Model):
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField()
    xp = fields.BigIntField(default=0)
    level = fields.IntField(default=0)
    last_xp_gain = fields.BigIntField(default=0)  # Timestamp for cooldown
    prestige = fields.IntField(default=0)

    class Meta:
        table = "userlevel"
        unique_together = ("user_id", "guild_id")

    def __str__(self):
        return f"User {self.user_id} in Guild {self.guild_id}: Level {self.level} (XP: {self.xp})"

class GuildLevelConfig(Model):
    guild_id = fields.BigIntField(pk=True)
    xp_cooldown = fields.IntField(default=20)  # Cooldown in seconds
    max_xp_per_message = fields.IntField(default=50)

class LevelReward(Model):
    guild_id = fields.BigIntField(pk=True)
    level = fields.IntField()
    role_id = fields.BigIntField()

    class Meta:
        unique_together = ("guild_id", "level")

class JailbreakPatterns(Model):
    pattern = fields.TextField()

    class Meta:
        table = "jailbreak_patterns"
    