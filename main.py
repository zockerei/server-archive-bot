import os
import time
import discord
import yaml
import logging.config
import requests
import secrets

# Intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Logging setup
with open('config.yaml', 'rt') as config_file:
    logging_config = yaml.safe_load(config_file.read())
    logging.config.dictConfig(logging_config['logging_config'])

discord_logger = logging.getLogger('discord')
bot_logger = logging.getLogger('bot.main')
bot_logger.info('Logging setup complete')

# Load bot configuration
with open('config.yaml') as config_file:
    bot_config = yaml.safe_load(config_file)
    bot_config = bot_config['bot_config']
    token, archiving, folder_path, channel_ids = (
        bot_config['token'],
        bot_config['archiving'],
        bot_config['folder_path'],
        bot_config['channel_ids']
    )
attachment_links_path = os.path.join(folder_path, 'links.log')
bot_logger.info('bot_config loaded')

# Create a set to store downloaded attachments' URLs
downloaded_attachments = set()

# Load downloaded attachments from file
if os.path.exists(attachment_links_path):
    with open(attachment_links_path, 'r') as attachments_file:
        downloaded_attachments = set(line.strip() for line in attachments_file)


@client.event
async def on_ready():
    """Handle the event when the bot is ready.

    This function logs in, sets up the database, adds words to the database,
    retrieves server member IDs and adds them to the database, and adds an admin user.
    """
    bot_logger.info(f'Logged in as {client.user}')
    bot_logger.info('Bot ready')

    if archiving:
        bot_logger.debug(f'Archiving pictures in these channels: {channel_ids}')
        await archive_pictures()


@client.event
async def on_message(message: discord.Message):
    """Downloads the attachment if the message is one

    Parameters:
        message (discord.Message): The message received by the bot.
    """
    if message.author == client.user:
        bot_logger.debug('Message from bot')
        return  # Ignore messages from the bot

    if message.channel.id in channel_ids:
        for attachment in message.attachments:
            download_attachment(attachment)


async def archive_pictures():
    """
    Archives attachments from specified channels.
    """
    try:
        for channel_id in channel_ids:
            bot_logger.debug(f'Channel_id: {channel_id}')
            channel = client.get_channel(channel_id)
            bot_logger.debug(f'Channel: {channel}')

            async for message in channel.history(limit=None):
                for attachment in message.attachments:
                    download_attachment(attachment)

            for thread in channel.threads:
                bot_logger.debug(f'Thread: {thread}')
                async for message in thread.history(limit=None):
                    for attachment in message.attachments:
                        download_attachment(attachment)

        bot_logger.info('Completed download of all attachments')

    except Exception as e:
        bot_logger.error(f"An error occurred: {e}")


def download_attachment(attachment):
    """Download an attachment and save it to a specified folder.

    Parameters:
        attachment: The attachment object to download.
    """
    if attachment.url in downloaded_attachments:
        bot_logger.info(f'Attachment {attachment.filename} has been downloaded before, skipping.')
        return

    bot_logger.info(f'Downloading attachment: {attachment.filename}')
    response = requests.get(attachment.url)

    # Random file name
    file_extension = os.path.splitext(attachment.filename)[1]
    random_filename = secrets.token_hex(10) + file_extension
    file_path = os.path.join(folder_path, random_filename)

    # Download to folder + add link to log file
    with open(file_path, 'wb') as output:
        output.write(response.content)
    bot_logger.info(f'Download complete: {attachment.filename}')
    time.sleep(1)

    # Add the attachment's URL to the set of downloaded attachments
    downloaded_attachments.add(attachment.url)

    # Save the attachment's URL to the file
    with open(attachment_links_path, 'a') as file:
        file.write(f'{attachment.url}\n')


client.run(token, log_handler=None)
