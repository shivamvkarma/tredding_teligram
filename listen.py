import logging
from telethon import TelegramClient, events
from config import *
import re
from fuzzywuzzy import fuzz
from datetime import datetime
from pytz import timezone

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set Mumbai's timezone (IST)
mumbai_tz = timezone('Asia/Kolkata')

# Create formatter
formatter = logging.Formatter('%(asctime)s [IST] - %(levelname)s - %(message)s')

# Create file handler
file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Define trading keywords
trading_keywords = {'bankex', 'Nifty', 'Sensex', 'MIDCAPNIFTY', 'BankNifty', 'FINNIFTY', 'buy', 'sell', 'ce', 'pe',
                    'above', 'near', 'dip', 'below', 'stoploss', 'sl', 'target', 'btst', 'ZERO TO HERO', 'herozero'}

can_mispell_words = {'bankex', 'nifty', 'sensex', 'midcapnifty', 'banknifty', 'finnifty', 'above'}


# Convert keywords to lowercase
trading_keywords = [keyword.lower() for keyword in trading_keywords]

# Channels allowed for processing
ALLOWED_CHANNEL_IDS = {
    -1001280552083, -1001604978873, -1001192950106, -1001824284028, -1001316378442,
    -1002069997090, -1001682621717, -1002130783441, -1001775776547, -1001667536105,
    -1001516168694, -1001749655427, 6892403211, -1001399054928, -1002072461678,
    -1001990796087, -1002109652078, -1001610199863, -1001204858813, -1001898280931,
    -1001403898599, -1001361867270, -1001600444335, -1001664030637, -1001280716846,
    -1001170839460
}

# Telethon client setup
client = TelegramClient('anon', api_id, api_hash)

def has_trading_keywords(message):
    # Convert message to lowercase for case-insensitive matching
    message = message.lower()

    # Count the number of trading keywords present in the message
    count = sum(keyword in message for keyword in trading_keywords)

    # Check if at least three trading keywords are present and a number greater than 10000
    if count >= 3:
        # Use regular expression to find numbers greater than 10000
        numbers = re.findall(r'\d+', message)
        for num in numbers:
            if int(num) > 10000:
                return True

    # Fuzzy matching for misspelled keywords
    for word in message.split():
        for keyword in trading_keywords:
            if fuzz.ratio(word, keyword) > 70:  # Adjust the threshold as needed
                count += 1
                if count >= 3:
                    return True

    return False


async def get_channel_info(channel_id):
    try:
        entity = await client.get_entity(channel_id)
        return f"@{entity.username}" if entity.username else entity.title
    except Exception as e:
        logging.error(f"Error getting channel info for ID {channel_id}: {e}")
        return None


@client.on(events.NewMessage)
async def my_event_handler(event):
    chat_id = event.chat_id
    message_text = event.raw_text

    # Check if the message is from an allowed channel
    if chat_id not in ALLOWED_CHANNEL_IDS:
        logging.info("Skipping message from non-allowed channel")
        return

    if len(message_text) > 200:
        logging.info("Skipping message due to length > 200 characters")
        return

    match = has_trading_keywords(message_text)

    if match:
        logging.info("Option call detected: %s", message_text)
        try:
            channel_name = await get_channel_info(chat_id)  # Change ID according to the need
            if channel_name:
                new_message_text = f'Given by {channel_name}: {message_text}'
            else:
                new_message_text = f'Given by channel: {message_text}'
            await client.send_message(-4274976924, new_message_text)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    else:
        logging.info("Not an option call: %s", message_text)


client.start()
client.run_until_disconnected()
