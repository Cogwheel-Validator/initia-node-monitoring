import aiohttp
import asyncio
import logging
import os
import yaml
from datetime import datetime

STATE_FILE = 'previous_state.yml'

def load_config(config_file):
    if not os.access(config_file, os.R_OK):
        raise ValueError(f"Cannot access configuration file: {config_file}")
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

async def fetch_status(session, url):
    try:
        async with session.get(f"{url}/status") as response:
            response.raise_for_status()
            data = await response.json()
            block_height = int(data['result']['sync_info']['latest_block_height'])
            return block_height
    except Exception as e:
        logging.error(f"Failed to get status from {url}: {e}")
        return None

async def check_status(rpc_urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_status(session, rpc['url']) for rpc in rpc_urls]
        heights = await asyncio.gather(*tasks)
        return [height for height in heights if height is not None]

async def compare_with_node(node_url, highest_height):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{node_url}/status") as response:
                response.raise_for_status()
                data = await response.json()
                node_height = int(data['result']['sync_info']['latest_block_height'])
                return highest_height - node_height
    except Exception as e:
        logging.error(f"Failed to get status from node {node_url}: {e}")
        return None

async def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

def load_previous_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as file:
            return yaml.safe_load(file)
    return {'previous_height_diff': None, 'last_alert_level': None}

def save_previous_state(height_diff, alert_level):
    state = {'previous_height_diff': height_diff, 'last_alert_level': alert_level}
    with open(STATE_FILE, 'w') as file:
        yaml.dump(state, file)

def determine_alert_level(height_diff, alert_levels):
    if height_diff >= alert_levels['level_5']:
        return 5
    elif height_diff >= alert_levels['level_4']:
        return 4
    elif height_diff >= alert_levels['level_3']:
        return 3
    elif height_diff >= alert_levels['level_2']:
        return 2
    elif height_diff >= alert_levels['level_1']:
        return 1
    else:
        return 0

async def alert(height_diff, alert_levels, telegram_config, previous_state):
    last_alert_level = previous_state['last_alert_level']
    previous_height_diff = previous_state['previous_height_diff']
    current_alert_level = determine_alert_level(height_diff, alert_levels)
    message = ""

    if current_alert_level > last_alert_level:
        message = f"Alert Level {current_alert_level}: Block height difference is {height_diff} blocks!"
    elif current_alert_level < last_alert_level and previous_height_diff is not None:
        message = f"Alert Level Improving to {current_alert_level}: Block height difference has decreased from {previous_height_diff} to {height_diff} blocks!"
    elif current_alert_level == last_alert_level:
        return  # No change in alert level, no need to send a message

    if message:
        logging.info(message)
        await send_telegram_message(telegram_config['bot_token'], telegram_config['chat_id'], message)
    
    # Save the new state
    save_previous_state(height_diff, current_alert_level)

async def periodic_check():
    telegram_config = load_config('config/telegram.yml')
    config = load_config('config/config.yml')

    rpc_urls = config['rpcs']
    node_url = config['node']['url']
    alert_levels = {
        'level_1': config['alerts'][0]['level_1'],
        'level_2': config['alerts'][1]['level_2'],
        'level_3': config['alerts'][2]['level_3'],
        'level_4': config['alerts'][3]['level_4'],
        'level_5': config['alerts'][4]['level_5']
    }

    while True:
        logging.info("Starting new check cycle.")
        heights = await check_status(rpc_urls)
        if heights:
            highest_height = max(heights)
            height_diff = await compare_with_node(node_url, highest_height)
            if height_diff is not None:
                previous_state = load_previous_state()
                await alert(height_diff, alert_levels, telegram_config, previous_state)
            else:
                # Alert if the node cannot be reached
                await send_telegram_message(
                    telegram_config['bot_token'], 
                    telegram_config['chat_id'], 
                    "Node is down or cannot be reached!"
                )
        else:
            # Alert if none of the RPC endpoints can be reached
            await send_telegram_message(
                telegram_config['bot_token'], 
                telegram_config['chat_id'], 
                "None of the RPC endpoints can be reached!"
            )
        await asyncio.sleep(15)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(periodic_check())
