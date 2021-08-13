import os
from dotenv import load_dotenv

load_dotenv()

username=os.getenv('bot_username')
passwd=os.getenv('bot_password')
client_id=os.getenv('praw_client_id')
client_secret=os.getenv('praw_client_secret')
refresh_token=os.getenv('praw_refresh_token')
