import prawcore
from collections import Counter
from io import BytesIO
import math
from PIL import Image
import asyncpraw
import asyncio
import json
import traceback
from urllib.error import HTTPError
import pytesseract
import yfinance as yf
import asyncprawcore
import requests
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import FirefoxOptions
from time import sleep
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import re
import concurrent.futures

import rsi
import config

tickerRE = re.compile(r"(?:\s)?([A-Z]{2,5})(?![a-z’'\.]+)(?:\s)?")

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

reddit = asyncpraw.Reddit(
    client_id=config.client_id,
    client_secret=config.client_secret,
    user_agent=f'Yolo (by u/{config.username})',
    refresh_token=config.refresh_token
)


async def stockInfo(comment, *args):
    arg = args[0][0]
    try:
        stock = yf.Ticker(arg)
        await comment.reply(f'```\n{str(arg).upper()}:\nAverage Vol.: {stock.info["averageDailyVolume10Day"]}\nVolume: {stock.info["volume"]}\nLast Close: {stock.info["previousClose"]}\nLast open: {stock.info["regularMarketOpen"]}\nMarket cap: {stock.info["marketCap"]}\nShares short: {stock.info["sharesShort"] if stock.info["sharesShort"] is not None else "N/A"}\n% Float short: {round(float(stock.info["shortPercentOfFloat"])*100, 2) if stock.info["shortPercentOfFloat"] is not None else "N/A"}%\nYTD Change: {round(float(stock.info["52WeekChange"])*100, 2)}%\n```')
    except ValueError:
        await comment.reply(f'Couldn\'t get info on {str(arg).upper()}')


async def stockPrice(comment, *args):
    arg = args[0][0]
    try:
        url = f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={arg}'
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'})
        data = {}
        try:
            data = json.loads(res.text)['quoteResponse']['result'][0]
            try:
                if 'marketState' in data.keys():
                    if data['marketState'] == 'PRE':
                        await comment.reply(f'Latest PM price of {str(arg).upper()}: {data["preMarketPrice"]}, {round(float(data["preMarketChangePercent"]), 3)}%')
                    elif data['marketState'] == 'REGULAR':
                        await comment.reply(f'Latest price of {str(arg).upper()}: {data["regularMarketPrice"]}, {round(float(data["regularMarketChangePercent"]), 3)}%')
                    elif data['marketState'] == 'POST':
                        await comment.reply(f'Latest AH price of {str(arg).upper()}: {data["postMarketPrice"]}, {round(float(data["postMarketChange"]), 3)}%')
                    else:
                        await comment.reply(f'Latest price of {str(arg).upper()}: {data["regularMarketPrice"]}, {round(float(data["regularMarketChangePercent"]), 3)}%')
                else:
                    try:
                        await comment.reply(f'{str(arg).upper()} last traded: {data["regularMarketPrice"]}, {round(float(data["regularMarketChangePercent"]), 3)}%')    
                    except KeyError:
                        await comment.reply(f'Error occurred while getting price of {str(arg).upper()}\n```{traceback.format_exc()}```\n<@510951917128646657> fix your shitty code.')
            except IndexError:
                await comment.reply(f'Error occurred while getting price of {str(arg).upper()}\n```{traceback.format_exc()}```\n<@510951917128646657> fix your shitty code.')
        except KeyError:
            await comment.reply(f'{str(arg).upper()} last traded: {data["regularMarketPrice"]}, {round(float(data["regularMarketChangePercent"]), 3)}%')
    except (TypeError, KeyError, IndexError) as err:
        await comment.reply(f'Couldn\'t get price of {str(arg).upper()}')


async def options(comment, *args):
    arg = args[0]
    option_type = {
        'call': 0,
        'put': 1
    }
    stock = yf.Ticker(arg[0])
    try:
        if option_type[str(arg[1]).lower()] == 0:
            response = stock.option_chain(arg[2])[0].loc[:, ~stock.option_chain(arg[2])[0].columns.isin(["contractSymbol", "lastTradeDate", "contractSize", "currency", "change", "percentChange"])].loc[stock.option_chain(arg[2])[0]["inTheMoney"] == False].head(5).to_markdown(index=False)
        else:
            response = stock.option_chain(arg[2])[1].loc[:, ~stock.option_chain(arg[2])[1].columns.isin(["contractSymbol", "lastTradeDate", "contractSize", "currency", "change", "percentChange"])].loc[stock.option_chain(arg[2])[1]["inTheMoney"] == False].tail(5).to_markdown(index=False)
    except IndexError:
        response = f'No Options Chain for {str(arg).upper()}\n```'
    await comment.reply(response)


async def getRSI(comment, *args):
    args = args[0]
    periods = ['max', '1mo', '2mo', '3mo', '6mo', '1y']
    if args[1] not in periods:
        comment.reply(f'Please choose a proper period format. Proper format is: {periods}')
        return
    await comment.reply(f'{rsi.run(args[0], args[1])}')


async def botHelp(comment, *args):
    arg = args[0][0]
    helpMenu = {
        'stockPrice': 'Return the current stock price of the ticker. Example:\n$stockPrice TSLA',
        'stockInfo': 'Get a small slice of information of the ticker. Example:\n$stockInfo TSLA',
        'options': 'Return the 5 closest OTM strikes for a specified expiry of a ticker. Examples:\n$options TSLA call 2021-08-20\n$options TSLA put 2021-08-20',
        'getRSI': 'Return RSI and SMA for supplied ticker in the supplied period. Example:\n$getRSI TSLA 1mo\nValid periods: max, 1mo, 2mo, 3mo, 6mo, 1y',
        'botHelp': 'Show this help'
    }
    try:
        await comment.reply(f'```\n{helpMenu[arg]}\n```')
    except:
        await comment.reply(f'Couldn\'t fetch help menu for: {arg}')

commands = {
    'stockPrice': stockPrice,
    'stockInfo': stockInfo,
    'options': options,
    'getRSI': getRSI,
    'botHelp': botHelp
}


async def run():
    sub = await reddit.subreddit('WeMakeMoney')
    async for comment in sub.stream.comments(skip_existing=True):
        c = str(comment.body)
        if '$' in c[0]:
            c = c.replace('\n', ' ')
            print(f'{datetime.now()} - Command: {c[1:].split(" ")[0]} - Params: {c[1:].split(" ")[1:]} - Comment: {comment}')
            if c[1:].split(' ')[0] in commands.keys():                
                try:
                    await commands[c[1:].split(' ')[0]](comment, c[1:].split(' ')[1:])
                except:
                    comment.reply(f'An error occurred. Contact the moderators of the sub.')
            else:
                comment.reply(f'Didn\'t understand command: {c[1:].split(" ")[0]}\n\nAvailable commands: {str(list(commands.keys())).replace("[", "").replace("]", "")}')


async def getPost(submission):
    try:
        options = FirefoxOptions()
        options.headless = True
        browser = webdriver.Firefox(options=options)
        browser.maximize_window()
        browser.get(f'https://www.reddit.com{submission.permalink}')
        element = browser.find_element('xpath', '//div[@data-test-id="post-content"]')
        location = element.location
        size = element.size
        total_height = element.size["height"]+1000
        browser.set_window_size(1920, total_height)
        sleep(1)
        png = browser.get_screenshot_as_png()
        img = Image.open(BytesIO(png))
        browser.quit()
        arr = BytesIO()
        img.save(arr, format='PNG')
        arr.seek(0)

        left = location['x'] + 270
        top = location['y']
        right = location['x'] + 270 + size['width']
        bottom = location['y'] + size['height']

        img = img.crop((math.floor(left), math.floor(top), math.ceil(right), math.ceil(bottom)))

        custom_conf = r'--oem 3 --psm 6'
        content = pytesseract.image_to_string(img, config=custom_conf)
    except NoSuchElementException:
        return None
    return content


async def checkTimer(submission):
    await asyncio.sleep(300)
    retest = await reddit.submission(submission)
    if retest.selftext == '[removed]':
        print(f'{datetime.now()} - Stop timer for {submission.title} - Discarded.')         
    else:
        print(f'{datetime.now()} - Stop timer for {submission.title} - Posting.')
        chain = 'N/A'
        stock = 'N/A'
        data2 = 'N/A'
        data = {}
        data2 = {}
        chain_track = ''
        likely_ticker = ''
        try:
            content = await getPost(submission)
            if content == None:
                return None
            elif len(content) < 1000:
                return None

            tickers = tickerRE.findall(content)
            tickers += tickerRE.findall(str(submission.title).upper())

            counters = Counter(list(filter(lambda x: x != 'DD', tickers)))
            most = counters.most_common(5)
            for ticker in most:
                try:
                    stock = yf.Ticker(ticker[0])
                    _ = stock.info['regularMarketOpen']
                    likely_ticker = ticker[0]
                    break
                except (KeyError, ValueError, HTTPError, IndexError):
                    continue

            try:
                chain = stock.options[0:3]
                response = f'\n```Snippet of Options Chain for {str(likely_ticker).upper()}\n'
                
                for item in chain:
                    response += f'EXP: {item}\n{stock.option_chain(item)[0].loc[:, ~stock.option_chain(item)[0].columns.isin(["contractSymbol", "lastTradeDate", "contractSize", "currency", "change", "percentChange"])].loc[stock.option_chain(item)[0]["inTheMoney"] == False].head(3)}\n'
                    chain_track += f'{stock.option_chain(item)[0].loc[:, ~stock.option_chain(item)[0].columns.isin(["contractSymbol", "lastTradeDate", "contractSize", "currency", "change", "percentChange"])].loc[stock.option_chain(item)[0]["inTheMoney"] == False].head(3)}\n'
            except IndexError:
                response = f'\n```No Options Chain for {str(likely_ticker).upper()}\n'

            url = f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={likely_ticker}'
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'})
            try:
                data = json.loads(res.text)['quoteResponse']['result'][0]
            except KeyError:
                data = data

            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{likely_ticker}?region=US&lang=en-US&includePrePost=false&interval=2m&useYfid=true&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'})
            data2 = json.loads(res.text)

        except IndexError:
            print(traceback.format_exc())
            return None

        try:
            volume_last = stock.info["volume"] if isinstance(stock, yf.Ticker) else stock
        except (KeyError, HTTPError):
            volume_last = "N/A"
        try:
            vol_10_avg = stock.info["averageVolume10days"] if isinstance(stock, yf.Ticker) else stock
        except (KeyError, HTTPError):
            vol_10_avg = "N/A"
        try:
            total = data2["chart"]["result"][0]["indicators"]["quote"][0]["volume"]
            last10 = data2["chart"]["result"][0]["indicators"]["quote"][0]["volume"][-10:]
            total = [0 if i is None else i for i in total]
            last10 = [0 if i is None else i for i in last10]

            avgTot = round(float(sum(total) / len(total)), 1)
            avg10 = round(float(sum(last10) / len(last10)), 1)
        except (KeyError, IndexError):
            avgTot = "N/A"
            avg10 = "N/A"
        

        try:
            if likely_ticker != '':
                #if stock.info["volume"] > stock.info["averageVolume10days"] and avg10 > avgTot:
                sub = await reddit.submission(submission)
                _ = await sub.crosspost(subreddit='WeMakeMoney', send_replies=False)
            else:
                return None           
        except AttributeError:
            pass

async def main():
    loop = asyncio.get_event_loop()
    funcs = [streamer(), run()]
    futures = [loop.create_task(func) for func in funcs]
    for result in await asyncio.gather(*futures):
        pass

async def streamer():
    sub = await reddit.subreddit('wallstreetbets')
    async for submission in sub.stream.submissions(skip_existing=True):
        try:
            if submission.link_flair_text == 'DD':                                
                print(f'{datetime.now()} - Start timer for {submission.title}')
                asyncio.create_task(checkTimer(submission))

        except (asyncprawcore.exceptions.RequestException, asyncio.exceptions.TimeoutError):
            continue


if __name__ == '__main__':
    while True:
        try:            
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        except (prawcore.exceptions.ServerError, prawcore.exceptions.ResponseException, asyncio.exceptions.TimeoutError):
            continue