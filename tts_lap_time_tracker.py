import os
import discord
from discord.ext import commands
from playwright.async_api import async_playwright
from gtts import gTTS
import asyncio

TOKEN = ""

# Enter the live timing URL of your karting track (Apex Timing Only Supported)
live_timing_url = ""

MONITOR_CHANNEL_ID = None # Enter Monitor Channel ID
MONITOR_VOICE_CHANNEL_ID = None # Enter the Voice Channel that you want it to read out the live times to
LOG_CHANNEL_ID = None # Enter the Log Channel ID, all logs will be sent here like errors

monitor_channel = None
monitor_voice_channel = None
log_channel = None

# Enter Driver Names that you want to monitor the live timing of
target_drivers = [""]
drivers_task = {}

bot_intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=bot_intents)
bot_voice_client = None

browser = None
page = None

tts_queue = asyncio.Queue()


async def setup_browser():
    global browser, page

    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    
    await page.goto(live_timing_url, timeout=30000)
    await page.wait_for_selector("td[data-type='dr']")

async def get_driver_last_lap(driver_name) -> str | None:
    global page

    driver_table = await page.query_selector_all("td[data-type='dr']")

    for cell in driver_table:
        name = (await cell.text_content()).strip().lower()

        if name == driver_name.lower():
            driver_data_id = await cell.get_attribute("data-id")
            
            if not driver_data_id:
                continue

            lap_data_id = driver_data_id.replace("c5", "c6")
            lap_cell = await page.query_selector(f"td[data-id='{lap_data_id}']")

            if lap_cell:
                return (await lap_cell.text_content()).strip()
    return None

async def monitor_driver(driver_name: str):
    last_lap = None

    while True:
        try:
            current_lap = await get_driver_last_lap(driver_name)

            if current_lap and current_lap != last_lap:
                last_lap = current_lap
                await monitor_channel.send(f"{driver_name} set a {current_lap}!")
                await tts_queue.put(f"{driver_name} {current_lap}")

            await asyncio.sleep(1)
        except Exception as e:
            error_message = f"Monitoring Error: {driver_name} {e}"

            if str(e).startswith("Page.query_selector_all: Target page, context or browser has been closed"):
                error_message += " Restarting Browser."
                await setup_browser()

            await log_channel.send(error_message)
            print(error_message)
            await asyncio.sleep(10)

async def join_voice_channel():
    global bot_voice_client

    try:
        if bot_voice_client.is_connected():
            return bot_voice_client
    except AttributeError:
        # We now Voice Channel obj does is None
        pass
    
    if not monitor_voice_channel:
        print("Could not find the voice channel!")
        return
    
    bot_voice_client = await monitor_voice_channel.connect()
    return bot_voice_client

async def tts_loop():
    global bot_voice_client
    bot_voice_client = await join_voice_channel()

    if not bot_voice_client:
        print("Could not connect to the voice channel!")
        return

    while True:
        text = await tts_queue.get()

        try:
            tts = gTTS(text=text, lang="en")
            tts_path = "tts_lap.mp3"
            tts.save(tts_path)

            if bot_voice_client.is_playing():
                bot_voice_client.stop()

            src = discord.FFmpegPCMAudio(tts_path)
            bot_voice_client.play(src)

            while bot_voice_client.is_playing():
                await asyncio.sleep(1)
            
            os.remove(tts_path)
        except Exception as e:
            error_message = f"TTS Error: {e}."

            if str(e).startswith("Not connected to voice"):
                await join_voice_channel()
                error_message += " Attempting re-join..."
            
            await log_channel.send(error_message)
            print(error_message)
    

async def setup_monitoring_drivers():
    await bot.wait_until_ready()

    if not monitor_channel or not monitor_voice_channel or not log_channel:
        print("Error Finding Channels!")
        return
    
    for driver in target_drivers:
        task = bot.loop.create_task(monitor_driver(driver))
        drivers_task[driver] = task

async def close_all_tasks_and_browser():
    global browser, bot_voice_client

    if browser:
        await browser.close()

    for task in drivers_task.values():
        task.cancel()

    await bot_voice_client.disconnect()
    bot_voice_client = None


@bot.command()
@commands.has_permissions(administrator=True)
async def start_monitoring_driver(ctx, *, new_driver: str):
    new_driver = new_driver.strip()

    if new_driver not in target_drivers:
        task = bot.loop.create_task(monitor_driver(new_driver))
        target_drivers.append(new_driver)
        drivers_task[new_driver] = task

        await log_channel.send(f"[i] Added Driver: {new_driver}")
    else:
        await log_channel.send(f"[i] {new_driver} is already being monitored!")

@bot.command()
@commands.has_permissions(administrator=True)
async def stop_monitoring_driver(ctx, *, driver: str):
    driver = driver.strip()

    task = drivers_task.get(driver)

    if task:
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            print(f"Cancelled Task for {driver}")

        del drivers_task[driver]
        target_drivers.remove(driver)

        await log_channel.send(f"[i] Stopped monitoring {driver}")
    else:
        await log_channel.send(f"[i] No active monitoring for {driver}")

@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    global browser, bot_voice_client

    await browser.close() 

    for task in drivers_task.values():
        task.cancel()

    await setup_browser()
    bot.loop.create_task(setup_monitoring_drivers())



    await log_channel.send("Browser Reset. Tasks Reset.")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    # Get Channels
    global monitor_channel, monitor_voice_channel, log_channel
    monitor_channel = bot.get_channel(MONITOR_CHANNEL_ID)
    monitor_voice_channel = bot.get_channel(MONITOR_VOICE_CHANNEL_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    await setup_browser()
    bot.loop.create_task(setup_monitoring_drivers())
    bot.loop.create_task(tts_loop())

@bot.event
async def on_disconnect():
    close_all_tasks_and_browser()


bot.run(TOKEN)