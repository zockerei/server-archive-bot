import discord
import yaml
import logging.config

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
    token, server_id, archiving, channel_ids = (
        bot_config['token'],
        bot_config['server_id'],
        bot_config['archiving'],
        bot_config['channel_ids']
    )
bot_logger.debug(f'{token} | {server_id} | {channel_ids}')
bot_logger.info('bot_config loaded')


@client.event
async def on_ready():
    """Handle the event when the bot is ready.

    This function logs in, sets up the database, adds words to the database,
    retrieves server member IDs and adds them to the database, and adds an admin user.
    """
    bot_logger.info(f'Logged in as {client.user}')

    if archiving:
        bot_logger.debug(f'Archiving pictures in these channels: {channel_ids}')
        await archive_pictures()

    bot_logger.info('Bot ready')


@client.event
async def on_message(message: discord.Message):
    """Handle the event when a message is received.

    This function processes all received messages, checks if they contain specific words,
    and performs corresponding actions such as updating word counts or handling commands.

    Parameters:
        message (discord.Message): The message received by the bot.
    """
    if message.author == client.user:
        bot_logger.debug('Message from bot')
        return  # Ignore messages from the bot

    for attachment in message.attachments:
        if attachment.url.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            bot_logger.debug(f'Attachment: {attachment}')


async def archive_pictures():
    """
    Archive attachments in the channels
    :return:
    """
    for channel_id in channel_ids:
        bot_logger.debug(f'channel_id: {channel_id}')
        channel = client.get_channel(channel_id)
        bot_logger.debug(f'channel: {channel}')
        async for message in channel.history(limit=None):
            for attachment in message.attachments:
                bot_logger.debug(f'Attachment: {attachment}')

client.run(token, log_handler=None)
