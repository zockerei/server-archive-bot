import os
import yaml
import logging.config
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Log file path
LOG_FOLDER_PATH = BASE_DIR / 'logs'
LOG_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_FOLDER_PATH = BASE_DIR / 'config'


class CustomFormatter(logging.Formatter):
    """
    Custom formatter to add colors to log messages.
    """
    COLORS = {
        'DEBUG': '\033[37m',       # White
        'INFO': '\033[32m',        # Green
        'WARNING': '\033[33m',     # Yellow
        'ERROR': '\033[31m',       # Red
        'CRITICAL': '\033[1;31m',  # Bold Red
        'NAME': '\033[36m'         # Cyan
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        name_color = self.COLORS['NAME']
        record.levelname = f"{log_color}{record.levelname:<8}{self.RESET}"
        record.name = f"{name_color}{record.name}{self.RESET}"
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logging():
    """
    Sets up the logging configuration for the application.

    Reads the logging configuration from a YAML file and applies it.
    Updates the log file paths for rotating and error logs.

    Raises:
        FileNotFoundError: If the logging configuration file is not found.
        yaml.YAMLError: If there is an error parsing the YAML file.
        Exception: For any other unexpected errors.
    """
    try:
        with open(CONFIG_FOLDER_PATH / 'logging_config.yaml', 'r') as file:
            config = yaml.safe_load(file.read())

        # Update file paths
        config['handlers']['rotating_file']['filename'] = str(LOG_FOLDER_PATH / 'bot.log')
        config['handlers']['error_file']['filename'] = str(LOG_FOLDER_PATH / 'errors.log')

        logging.config.dictConfig(config)
    except FileNotFoundError:
        print(f"Logging configuration file not found: {CONFIG_FOLDER_PATH / 'logging_config.yaml'}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
    except Exception as e:
        print(f"Unexpected error in Logging Configuration: {e}")


def load_downloaded_attachments(attachment_links_path):
    """Loads a set of downloaded attachment URLs from a file.

    Returns:
        set: A set of URLs of downloaded attachments.
    """
    if os.path.exists(attachment_links_path):
        with open(attachment_links_path, 'r') as attachments_file:
            return set(line.strip() for line in attachments_file)
    return set()


class BotConfig:
    """
    Singleton class to load and provide bot configuration.

    Attributes:
        token (str): The bot token.
        words (list): A list of words to track.
        server_id (int): The ID of the server.
        channel_id (int): The ID of the channel.
        admin_ids (list): A list of admin user IDs.
        disable_initial_scan (bool): Flag to disable initial scan.
    """

    _instance = None

    def __new__(cls):
        """
        Creates a new instance of BotConfig if it doesn't exist.

        Returns:
            BotConfig: The singleton instance of BotConfig.
        """
        if cls._instance is None:
            cls._instance = super(BotConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """
        Loads configuration from a YAML file.

        Raises:
            FileNotFoundError: If the bot configuration file is not found.
            yaml.YAMLError: If there is an error parsing the YAML file.
            Exception: For any other unexpected errors.
        """
        try:
            with open(CONFIG_FOLDER_PATH / 'bot_config.yaml', 'r') as config_file:
                config = yaml.safe_load(config_file)
                self.token = config['token']
                self.folder_path = config['folder_path']
                self.channel_ids = config['channel_ids']
                self.archiving = config['archiving']
        except FileNotFoundError:
            logging.error(f"Bot configuration file not found: {CONFIG_FOLDER_PATH / 'bot_config.yaml'}")
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in Bot Configuration: {e}")


def get_bot_config():
    """
    Gets the singleton instance of BotConfig.

    Returns:
        BotConfig: The singleton instance of BotConfig.
    """
    return BotConfig()
