import os
import yaml
import logging.config

# Function to load the logging configuration
def setup_logging(default_path='logging_config.yaml'):
    """Setup logging configuration"""
    try:
        with open(default_path, 'r') as file:
            config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)
    except FileNotFoundError:
        print(f"Logging configuration file not found: {default_path}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
    except Exception as e:
        print(f"Unexpected error in Logging Configuration: {e}")

# Function to load the bot configuration
def load_bot_config():
    """Loads bot configuration from a YAML file.

    Returns:
        tuple: A tuple containing the bot token, archiving status, folder path, and channel IDs.
    """
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
        bot_config = config['bot_config']
        
        token = bot_config['token']
        archiving = bot_config['archiving']
        folder_path = bot_config['folder_path']
        channel_ids = bot_config['channel_ids']

    return token, archiving, folder_path, channel_ids

# Function to load downloaded attachments from file
def load_downloaded_attachments(attachment_links_path):
    """Loads a set of downloaded attachment URLs from a file.

    Args:
        attachment_links_path (str): The file path to the attachment links file.

    Returns:
        set: A set of URLs of downloaded attachments.
    """
    if os.path.exists(attachment_links_path):
        with open(attachment_links_path, 'r') as attachments_file:
            return set(line.strip() for line in attachments_file)
    return set()
