import os
import discord
from discord.ext import commands
import logging
from config import setup_logging, get_bot_config, load_downloaded_attachments
from cogs.events import BotEvents
import asyncio

# Setup logging with the specified configuration path
setup_logging()
bot_logger = logging.getLogger('bot')
bot_logger.info('Logging setup complete')

# Intents
intents = discord.Intents.default()
intents.message_content = True
bot_logger.debug(f'Intents setup complete: {intents}')

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Load bot configuration with the specified configuration path
bot.config = get_bot_config()
bot.attachment_links_path = os.path.join(bot.config.folder_path, 'links.log')
bot_logger.info('Bot configuration loaded')

# Create a set to store downloaded attachments' URLs
bot.downloaded_attachments = load_downloaded_attachments(bot.attachment_links_path)


async def main():
    """
    Loads all cog extensions and starts the Discord bot.
    """
    await bot.add_cog(BotEvents(bot))
    await bot.start(bot.config.token)


asyncio.run(main())
