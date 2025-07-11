# Live Timing Kart Lap Time TTS (Apex Timing Support Only)

This is my own personal project. I would use this at my local karting track so that I could hear my live time while on track. The bot will connect to a voice channel that you specifiy and monitor the live timing website and wait for your lap time and then send the lap time to the monitor channel and read it out in the voice channel. 

NOTE: This is my own project that I did not intend to release so it might be prone to bugs. I have not vigorously tested this so for any bugs please submit an issue and I will fix it accordingly. 


## Installation

### Go to the project directory

```bash
  cd project/
```

### Download and setup ffmpeg (REQUIRED)

** The exe is not included due to the potential for malware to be disturbuted. Do not run random exes on peoples GitHub projects **

Download ffmpeg https://ffmpeg.org/download.html and drag the executable into the same directory as the script **or it will not work**

Windows: Drag ffmpeg.exe into the same directory that the tts_lap_time_tracker.py script is in

### Install dependencies

```bash
pip install discord.py playwright gtts asyncio
```

After they have all installed

```bash
playwright install
```

### Start the script

```bash
python tts_lap_time_tracker.py
```


## Required Configuration of Script

| Variable | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `TOKEN` | `string` | **Required**. Your Discord Bot Token |
| `live_timing_url` | `string` | **Required**. The Live Timing URL. Example: https://live.apex-timing.com/kartingname |
| `MONITOR_CHANNEL_ID` | `Int` | **Required**. Your Discord Monitor Channel ID |
| `MONITOR_VOICE_CHANNEL_ID` | `Int` | **Required**. Your Discord Monitor Voice Channel ID |
| `LOG_CHANNEL_ID` | `Int` | **Required**. Your Discord Log Channel ID (This will send all errors to the discord channel) |
| `target_drivers` | `List: string` | **Required**. The Driver Name(s) of the live timings you want to monitor/log.|



## Authors

- [@jacobkulik](https://github.com/jacobkulik)


## Demo

I will upload soon


## Support

Join the discord: https://discord.gg/xt2sGbyvrD

