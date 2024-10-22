import os
import discord
import requests
import secrets
import logging
from config import setup_logging, load_bot_config, load_downloaded_attachments

# Intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Setup logging
setup_logging()
discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.info('Logging setup complete')

# Load bot configuration
token, archiving, folder_path, channel_ids = load_bot_config()
attachment_links_path = os.path.join(folder_path, 'links.log')
bot_logger.info('Bot configuration loaded')

# Create a set to store downloaded attachments' URLs
downloaded_attachments = load_downloaded_attachments(attachment_links_path)

@client.event
async def on_ready():
    """Logs bot readiness and initiates archiving if enabled."""
    bot_logger.info(f'Logged in as {client.user}')
    bot_logger.info('Bot ready')

    if archiving:
        bot_logger.debug(f'Archiving pictures in these channels: {channel_ids}')
        await archive_pictures()

@client.event
async def on_message(message: discord.Message):
    """Handles incoming messages and downloads attachments if applicable.

    Args:
        message (discord.Message): The message object from Discord.
    """
    if message.author == client.user:
        return

    if message.channel.id in channel_ids:
        for attachment in message.attachments:
            download_attachment(attachment)

async def archive_pictures():
    """Archives pictures from specified channels and their threads."""
    try:
        for channel_id in channel_ids:
            channel = client.get_channel(channel_id)
            async for message in channel.history(limit=None):
                for attachment in message.attachments:
                    download_attachment(attachment)

            for thread in channel.threads:
                async for message in thread.history(limit=None):
                    for attachment in message.attachments:
                        download_attachment(attachment)

        bot_logger.info('Completed download of all attachments')
    except Exception as e:
        bot_logger.error(f"An error occurred: {e}")

def download_attachment(attachment):
    """Downloads an attachment if it hasn't been downloaded already.

    Args:
        attachment (discord.Attachment): The attachment object from Discord.
    """
    if attachment.url in downloaded_attachments:
        return

    response = requests.get(attachment.url)
    file_extension = os.path.splitext(attachment.filename)[1]
    random_filename = secrets.token_hex(10) + file_extension
    file_path = os.path.join(folder_path, random_filename)

    with open(file_path, 'wb') as output:
        output.write(response.content)

    downloaded_attachments.add(attachment.url)
    with open(attachment_links_path, 'a') as file:
        file.write(f'{attachment.url}\n')

client.run(token, log_handler=None)
