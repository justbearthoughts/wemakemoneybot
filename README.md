# wemakemoneybot

This bot aids running the Reddit sub [r/WeMakeMoney](https://www.reddit.com/r/WeMakeMoney/).
The sub came about from a group of tight people from OG WSB and the post-GME different splinter subs.

## Setup

Install requirements by doing `pip install --user -r requirements.txt`.
Using a virtual environment is recommended!

Create a new reddit account to act as your developer bot.
You can get the praw client and secret ID by creating a new app (go to preferences > apps > create new app).
Choose a web app and set redirect URI to http://localhost:8080.

Create a `.env` file in the repo containing the following variables for your developer bot account.
The initial `.env` file looks as such:
```
bot_username=<bot account username>
bot_password=<bot account password>
praw_client_id=<client id>
praw_client_secret=<client secret key>
```

Then, run `python praw/obtain_refresh_token.py`.
When prompted for scopes, enter the desired permissions or enter * for all permissions.
Do not leave this prompt blank, or reddit will throw a very uninformative error once you follow the link.
Follow the link that the script returns and accept the OAUTH2 scopes if you still agree with them.
Your browser will redirect you to a page on `localhost:8080`, copy the refresh token.
Add the refresh token to your `.env` file as `praw_refresh_token=<refresh token>`.

Finally, add the target subreddit for the bot to the `.env` with `subreddit=<target subreddit>`.
The bot will monitor comments posted to this subreddit to look for bot commands from subreddit users.

It is useful to setup a private subreddit for development purposes only, so this target subreddit may change for development vs. production.

## To run as a script

Activate virtual environment if one is being used.
Create a `config.py` as described below in "To run as a service section".
Run the bot with `python wemakemoneybot.py`.

## To run as a service

Install and follow the output provided by install.sh.
The `config.py` looks as such:
```python
username = 'username'
passwd = 'password123'
client_id = 'some_id'
client_secret = 'very_secret'
refresh_token= 'long_token'
```