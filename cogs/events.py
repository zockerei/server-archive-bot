import discord
from discord.ext import commands
import logging
import os
import requests
import secrets


class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_logger = logging.getLogger('bot.events')

    @commands.Cog.listener()
    async def on_ready(self):
        """Logs bot readiness and initiates archiving if enabled."""
        self.bot_logger.info(f'Logged in as {self.bot.user}')
        self.bot_logger.info('Bot ready')

        if self.bot.config.archiving:
            self.bot_logger.debug(f'Archiving pictures in these channels: {self.bot.config.channel_ids}')
            try:
                await self.archive_pictures()
            except Exception as e:
                self.bot_logger.error(f"Error during archiving: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handles incoming messages and downloads attachments if applicable."""
        if message.author == self.bot.user:
            self.bot_logger.debug('Ignoring message from self')
            return

        # Check if the message is in a monitored channel or its thread
        if (message.channel.id in self.bot.config.channel_ids or
           (message.channel.parent and message.channel.parent.id in self.bot.config.channel_ids)):
            channel_name = message.channel.name
            thread_name = message.channel.name if isinstance(message.channel, discord.Thread) else None
            self.bot_logger.debug(f'Message is in a monitored channel or thread: {message.channel.id}')

            for attachment in message.attachments:
                self.bot_logger.debug(f'Found attachment: {attachment.filename}')
                try:
                    self.download_attachment(attachment, channel_name, thread_name)
                except Exception as e:
                    self.bot_logger.error(f"Error downloading attachment {attachment.filename}: {e}")

    async def archive_pictures(self):
        """Archives pictures from specified channels and their threads."""
        try:
            for channel_id in self.bot.config.channel_ids:
                channel = self.bot.get_channel(channel_id)
                if channel is None:
                    self.bot_logger.warning(f'Channel with ID {channel_id} not found')
                    continue

                channel_name = channel.name
                self.bot_logger.debug(f'Accessing channel: {channel_id}')
                async for message in channel.history(limit=None):
                    for attachment in message.attachments:
                        self.bot_logger.debug(f'Found attachment in history: {attachment.filename}')
                        try:
                            self.download_attachment(attachment, channel_name)
                        except Exception as e:
                            self.bot_logger.error(
                                f"Error downloading attachment {attachment.filename} from history: {e}"
                            )

                for thread in channel.threads:
                    thread_name = thread.name
                    self.bot_logger.debug(f'Accessing thread: {thread.name}')
                    async for message in thread.history(limit=None):
                        for attachment in message.attachments:
                            self.bot_logger.debug(f'Found attachment in thread history: {attachment.filename}')
                            try:
                                self.download_attachment(attachment, channel_name, thread_name)
                            except Exception as e:
                                self.bot_logger.error(
                                    f"Error downloading attachment {attachment.filename} from thread history: {e}"
                                )

            self.bot_logger.info('Completed download of all attachments')
        except Exception as e:
            self.bot_logger.error(f"An error occurred during archiving: {e}")

    def download_attachment(self, attachment, channel_name, thread_name=None):
        """Downloads an attachment if it hasn't been downloaded already, organizing by channel and thread."""
        if attachment.url in self.bot.downloaded_attachments:
            self.bot_logger.debug(f'Attachment already downloaded: {attachment.url}')
            return

        # Create directory path based on channel and thread names
        directory_path = os.path.join(self.bot.config.folder_path, channel_name)
        if thread_name:
            directory_path = os.path.join(directory_path, thread_name)

        # Ensure the directory exists
        os.makedirs(directory_path, exist_ok=True)

        self.bot_logger.info(f'Downloading attachment: {attachment.filename}')
        try:
            response = requests.get(attachment.url)
            response.raise_for_status()  # Raise an error for bad responses
            file_extension = os.path.splitext(attachment.filename)[1]
            random_filename = secrets.token_hex(10) + file_extension
            file_path = os.path.join(directory_path, random_filename)

            with open(file_path, 'wb') as output:
                output.write(response.content)
            self.bot_logger.info(f'Attachment saved as: {random_filename}')

            self.bot.downloaded_attachments.add(attachment.url)
            with open(self.bot.attachment_links_path, 'a') as file:
                file.write(f'{attachment.url}\n')
            self.bot_logger.debug(f'Attachment URL logged: {attachment.url}')
        except requests.RequestException as e:
            self.bot_logger.error(f"Failed to download attachment {attachment.filename}: {e}")


def setup(bot):
    bot.add_cog(BotEvents(bot))
