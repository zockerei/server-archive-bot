import os
import discord
import requests
import secrets
import logging
from config import setup_logging, get_bot_config, load_downloaded_attachments

# Setup logging with the specified configuration path
setup_logging()
bot_logger = logging.getLogger('bot')
bot_logger.info('Logging setup complete')

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot_logger.debug(f'Intents setup complete: {intents}')
client = discord.Client(intents=intents)

# Load bot configuration with the specified configuration path
config = get_bot_config()
attachment_links_path = os.path.join(config.folder_path, 'links.log')
bot_logger.info('Bot configuration loaded')

# Create a set to store downloaded attachments' URLs
downloaded_attachments = load_downloaded_attachments(attachment_links_path)


@client.event
async def on_ready():
    """Logs bot readiness and initiates archiving if enabled."""
    bot_logger.info(f'Logged in as {client.user}')
    bot_logger.info('Bot ready')

    if config.archiving:
        bot_logger.debug(f'Archiving pictures in these channels: {config.channel_ids}')
        try:
            await archive_pictures()
        except Exception as e:
            bot_logger.error(f"Error during archiving: {e}")


@client.event
async def on_message(message: discord.Message):
    """Handles incoming messages and downloads attachments if applicable.

    Args:
        message (discord.Message): The message object from Discord.
    """
    if message.author == client.user:
        bot_logger.debug('Ignoring message from self')
        return

    # Check if the message is in a monitored channel or its thread
    if (message.channel.id in config.channel_ids or
       (message.channel.parent and message.channel.parent.id in config.channel_ids)):
        channel_name = message.channel.name
        thread_name = message.channel.name if isinstance(message.channel, discord.Thread) else None
        bot_logger.debug(f'Message is in a monitored channel or thread: {message.channel.id}')

        for attachment in message.attachments:
            bot_logger.debug(f'Found attachment: {attachment.filename}')
            try:
                download_attachment(attachment, channel_name, thread_name)
            except Exception as e:
                bot_logger.error(f"Error downloading attachment {attachment.filename}: {e}")


async def archive_pictures():
    """Archives pictures from specified channels and their threads."""
    try:
        for channel_id in config.channel_ids:
            channel = client.get_channel(channel_id)
            if channel is None:
                bot_logger.warning(f'Channel with ID {channel_id} not found')
                continue

            channel_name = channel.name
            bot_logger.debug(f'Accessing channel: {channel_id}')
            async for message in channel.history(limit=None):
                for attachment in message.attachments:
                    bot_logger.debug(f'Found attachment in history: {attachment.filename}')
                    try:
                        download_attachment(attachment, channel_name)
                    except Exception as e:
                        bot_logger.error(f"Error downloading attachment {attachment.filename} from history: {e}")

            for thread in channel.threads:
                thread_name = thread.name
                bot_logger.debug(f'Accessing thread: {thread.name}')
                async for message in thread.history(limit=None):
                    for attachment in message.attachments:
                        bot_logger.debug(f'Found attachment in thread history: {attachment.filename}')
                        try:
                            download_attachment(attachment, channel_name, thread_name)
                        except Exception as e:
                            bot_logger.error(f"Error downloading attachment {attachment.filename} from thread history: {e}")

        bot_logger.info('Completed download of all attachments')
    except Exception as e:
        bot_logger.error(f"An error occurred during archiving: {e}")


def download_attachment(attachment, channel_name, thread_name=None):
    """Downloads an attachment if it hasn't been downloaded already, organizing by channel and thread.

    Args:
        attachment (discord.Attachment): The attachment object from Discord.
        channel_name (str): The name of the channel.
        thread_name (str, optional): The name of the thread, if applicable.
    """
    if attachment.url in downloaded_attachments:
        bot_logger.debug(f'Attachment already downloaded: {attachment.url}')
        return

    # Create directory path based on channel and thread names
    directory_path = os.path.join(config.folder_path, channel_name)
    if thread_name:
        directory_path = os.path.join(directory_path, thread_name)

    # Ensure the directory exists
    os.makedirs(directory_path, exist_ok=True)

    bot_logger.info(f'Downloading attachment: {attachment.filename}')
    try:
        response = requests.get(attachment.url)
        response.raise_for_status()  # Raise an error for bad responses
        file_extension = os.path.splitext(attachment.filename)[1]
        random_filename = secrets.token_hex(10) + file_extension
        file_path = os.path.join(directory_path, random_filename)

        with open(file_path, 'wb') as output:
            output.write(response.content)
        bot_logger.info(f'Attachment saved as: {random_filename}')

        downloaded_attachments.add(attachment.url)
        with open(attachment_links_path, 'a') as file:
            file.write(f'{attachment.url}\n')
        bot_logger.debug(f'Attachment URL logged: {attachment.url}')
    except requests.RequestException as e:
        bot_logger.error(f"Failed to download attachment {attachment.filename}: {e}")


client.run(config.token, log_handler=None)
