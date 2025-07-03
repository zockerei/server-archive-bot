import discord
from discord.ext import commands
import logging
import requests
import secrets
from pathlib import Path


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

        is_monitored = message.channel.id in self.bot.config.channel_ids

        # If not in monitored channel, check if it's a thread of a monitored channel
        if not is_monitored and hasattr(message.channel, 'parent'):
            is_monitored = message.channel.parent and message.channel.parent.id in self.bot.config.channel_ids
            self.bot_logger.debug(f'Message is in a thread of a monitored channel: {message.channel.id}')

        if is_monitored:
            channel_name = message.channel.name
            thread_name = message.channel.name if hasattr(message.channel, 'parent') else None
            self.bot_logger.debug(f'Message is in a monitored channel or thread: {message.channel.id}')

            for attachment in message.attachments:
                self.bot_logger.info(f'Found attachment: {attachment.filename}')
                try:
                    self.download_attachment(attachment, message.channel, channel_name, thread_name)
                except Exception as e:
                    self.bot_logger.error(f"Error downloading attachment {attachment.filename}: {e}")
        else:
            self.bot_logger.debug(f'Message is not in a monitored channel or thread: {message.channel.id}')

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
                            self.download_attachment(attachment, channel, channel_name)
                        except Exception as e:
                            self.bot_logger.error(
                                f"Error downloading attachment {attachment.filename} from history: {e}"
                            )

                # Handle threads
                for thread in channel.threads:
                    thread_name = thread.name
                    self.bot_logger.debug(f'Accessing thread: {thread.name}')
                    async for message in thread.history(limit=None):
                        for attachment in message.attachments:
                            self.bot_logger.debug(f'Found attachment in thread history: {attachment.filename}')
                            try:
                                self.download_attachment(attachment, channel, channel_name, thread_name)
                            except Exception as e:
                                self.bot_logger.error(
                                    f"Error downloading attachment {attachment.filename} from thread history: {e}"
                                )

            self.bot_logger.info('Completed download of all attachments')
        except Exception as e:
            self.bot_logger.error(f"An error occurred during archiving: {e}")

    def download_attachment(self, attachment, channel, channel_name: str, thread_name: str = None):
        """Downloads an attachment if it hasn't been downloaded already."""
        # Check if already downloaded using database
        if self.bot.db_manager.is_downloaded(attachment.url):
            self.bot_logger.debug(f'Attachment already downloaded: {attachment.url}')
            return

        # Create directory path based on channel and thread names
        directory_path = Path(self.bot.config.folder_path) / channel_name
        if thread_name:
            directory_path = directory_path / thread_name

        # Ensure the directory exists
        directory_path.mkdir(parents=True, exist_ok=True)

        self.bot_logger.info(f'Downloading attachment: {attachment.filename}')
        
        try:
            response = requests.get(attachment.url, timeout=30)
            response.raise_for_status()
            
            # Generate random filename with original extension
            file_extension = Path(attachment.filename).suffix
            random_filename = f"{secrets.token_hex(10)}{file_extension}"
            file_path = directory_path / random_filename

            # Write file
            with open(file_path, 'wb') as output:
                output.write(response.content)
            
            # Add to database
            success = self.bot.db_manager.add_attachment(
                url=attachment.url,
                filename=attachment.filename,
                channel_id=channel.id
            )
            
            if success:
                self.bot_logger.info(f'Attachment saved as: {random_filename}')
            else:
                self.bot_logger.debug(f'Attachment URL already in database: {attachment.url}')
                
        except requests.RequestException as e:
            self.bot_logger.error(f"Failed to download attachment {attachment.filename}: {e}")
        except OSError as e:
            self.bot_logger.error(f"Failed to save attachment {attachment.filename}: {e}")
        except Exception as e:
            self.bot_logger.error(f"Unexpected error downloading {attachment.filename}: {e}")


def setup(bot):
    bot.add_cog(BotEvents(bot))
