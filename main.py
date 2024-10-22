import os
import discord
import requests
import secrets
import logging
from config.config import setup_logging, load_bot_config, load_downloaded_attachments

# Intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Setup logging with the specified configuration path
setup_logging()
discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.info('Logging setup complete')

# Load bot configuration with the specified configuration path
token, archiving, folder_path, channel_ids = load_bot_config()
attachment_links_path = os.path.join(folder_path, 'logs/links.log')
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
        bot_logger.debug(f'Message is in a monitored channel: {message.channel.id}')
        for attachment in message.attachments:
            bot_logger.debug(f'Found attachment: {attachment.filename}')
            download_attachment(attachment)

async def archive_pictures():
    """Archives pictures from specified channels and their threads."""
    try:
        for channel_id in channel_ids:
            bot_logger.debug(f'Accessing channel: {channel_id}')
            channel = client.get_channel(channel_id)
            async for message in channel.history(limit=None):
                for attachment in message.attachments:
                    bot_logger.debug(f'Found attachment in history: {attachment.filename}')
                    download_attachment(attachment)

            for thread in channel.threads:
                bot_logger.debug(f'Accessing thread: {thread.name}')
                async for message in thread.history(limit=None):
                    for attachment in message.attachments:
                        bot_logger.debug(f'Found attachment in thread history: {attachment.filename}')
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
        bot_logger.debug(f'Attachment already downloaded: {attachment.url}')
        return

    bot_logger.info(f'Downloading attachment: {attachment.filename}')
    response = requests.get(attachment.url)
    file_extension = os.path.splitext(attachment.filename)[1]
    random_filename = secrets.token_hex(10) + file_extension
    file_path = os.path.join(folder_path, random_filename)

    with open(file_path, 'wb') as output:
        output.write(response.content)
    bot_logger.info(f'Attachment saved as: {random_filename}')

    downloaded_attachments.add(attachment.url)
    with open(attachment_links_path, 'a') as file:
        file.write(f'{attachment.url}\n')
    bot_logger.debug(f'Attachment URL logged: {attachment.url}')

client.run(token, log_handler=None)
