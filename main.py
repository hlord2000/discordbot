import os
import asyncio
from dotenv import load_dotenv
import hikari
import lightbulb
import miru

# Load environment variables from .env file
load_dotenv()

# Get bot token and guild ID from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', '1107498977814904833'))

bot = lightbulb.BotApp(
    token=BOT_TOKEN,
    default_enabled_guilds=(GUILD_ID,)
)

# Wrap the bot in a miru client
miru_client = miru.Client(bot)

class QueueView(miru.View):
    def __init__(self, role_mention: str):
        super().__init__(timeout=None)  # Set timeout to None for persistent view
        self.queue = []
        self.role_mention = role_mention

    @miru.button(label="Join Queue", style=hikari.ButtonStyle.PRIMARY)
    async def join_queue(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if ctx.user.id not in self.queue:
            self.queue.append(ctx.user.id)
            await self.update_message(ctx)
        await ctx.defer()

    @miru.button(label="Leave Queue", style=hikari.ButtonStyle.DANGER)
    async def leave_queue(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if ctx.user.id in self.queue:
            self.queue.remove(ctx.user.id)
            await self.update_message(ctx)
        await ctx.defer()

    async def update_message(self, ctx: miru.ViewContext) -> None:
        queue_list = "\n".join([f"{i+1}. <@{user_id}>" for i, user_id in enumerate(self.queue)])
        content = f"{self.role_mention}Current Queue ({len(self.queue)} members):\n{queue_list}"
        await ctx.message.edit(content=content)

@bot.command
@lightbulb.option("role", "The role to mention", type=hikari.Role, required=True)
@lightbulb.option("timeout", "Time in minutes after which the queue message will be deleted", type=int, required=False, min_value=1)
@lightbulb.command("start_queue", "Start a new game queue")
@lightbulb.implements(lightbulb.SlashCommand)
async def start_queue(ctx: lightbulb.Context) -> None:
    role_mention = ctx.options.role.mention
    view = QueueView(role_mention)
    
    content = f"{role_mention}A new queue has started! Click the button to join or leave the queue!"
    message = await ctx.respond(content, components=view.build())
    miru_client.start_view(view)

    if ctx.options.timeout:
        await asyncio.sleep(ctx.options.timeout * 60)
        await message.delete()
        view.stop()

@bot.command
@lightbulb.command("clean", "Delete all of the bot's previous messages")
@lightbulb.implements(lightbulb.SlashCommand)
async def clean(ctx: lightbulb.Context) -> None:
    # Get the channel from the context
    channel = ctx.get_channel()
    
    # Fetch the last 100 messages in the channel
    messages = await ctx.app.rest.fetch_messages(channel)
    
    # Filter messages sent by the bot
    bot_messages = [msg for msg in messages if msg.author.id == ctx.app.get_me().id]
    
    # Delete bot messages
    for msg in bot_messages:
        await ctx.app.rest.delete_message(channel, msg)
    
    # Send a confirmation message and delete it after 5 seconds
    await ctx.respond(f"Deleted {len(bot_messages)} bot messages.", flags=hikari.MessageFlag.EPHEMERAL)

bot.run()
