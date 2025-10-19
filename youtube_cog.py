import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import requests
import dateutil.parser

YOUTUBE_DB = "youtube.json"

def load_yt_data():
    if not os.path.exists(YOUTUBE_DB): return {}
    try:
        with open(YOUTUBE_DB, "r", encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError: return {}

def save_yt_data(data):
    with open(YOUTUBE_DB, "w", encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

class YouTubeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_youtube.start()

    def cog_unload(self):
        self.check_youtube.cancel()

    @app_commands.command(name="youtube", description="ამატებს YouTube არხს შეტყობინებებისთვის")
    @app_commands.describe(
        youtube_channel_id="არხის ID (მაგ: UClgRkhTL3_hImCAmdLfDE4g)",
        discord_channel="არხი სადაც დაიდება შეტყობინება",
        notify_type="რა შეტყობინება გაიგზავნოს"
    )
    @app_commands.choices(notify_type=[
        app_commands.Choice(name="მხოლოდ ვიდეოები", value="video"),
        app_commands.Choice(name="მხოლოდ ლაივები", value="live"),
        app_commands.Choice(name="ორივე", value="both")
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def add_youtube(self, interaction: discord.Interaction, youtube_channel_id: str, discord_channel: discord.TextChannel, notify_type: str):
        data = load_yt_data()
        guild_id = str(interaction.guild.id)
        if guild_id not in data: data[guild_id] = {}
        data[guild_id][youtube_channel_id] = {
            "discord_channel_id": discord_channel.id, "notify_type": notify_type,
            "last_video_id": None, "is_live": False
        }
        save_yt_data(data)
        await interaction.response.send_message(f"არხი `{youtube_channel_id}` დაემატა #{discord_channel.name}-ში გაიგზავნება", ephemeral=True)

    # YouTube-ის წაშლის ბრძანება (სურვილისამებრ, თუ გინდა დატოვე)
    @app_commands.command(name="youtube-remove", description="შლის YouTube არხს სიიდან")
    @app_commands.describe(youtube_channel_id="არხის ID რომლის წაშლა გინდა")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove_youtube(self, interaction: discord.Interaction, youtube_channel_id: str):
        data = load_yt_data()
        guild_id = str(interaction.guild.id)
        if guild_id in data and youtube_channel_id in data[guild_id]:
            del data[guild_id][youtube_channel_id]
            save_yt_data(data)
            await interaction.response.send_message(f"არხი `{youtube_channel_id}` წაიშალა", ephemeral=True)
        else: await interaction.response.send_message("ეს არხი არ არის დამატებული", ephemeral=True)

    # --- ფონური პროცესი ---
    @tasks.loop(minutes=2)
    async def check_youtube(self):
        await self.bot.wait_until_ready()
        yt_api_key = os.environ.get('YOUTUBE_API_KEY')
        if not yt_api_key: return # ჩუმად ვჩერდებით თუ გასაღები არაა

        data = load_yt_data()
        for guild_id, channels in data.items():
            for yt_id, config in channels.items():
                discord_channel_id = config.get("discord_channel_id")
                notify_type = config.get("notify_type", "both")
                channel = self.bot.get_channel(discord_channel_id)
                if not channel: continue

                # ვიდეოები
                if notify_type in ["video", "both"]:
                    try:
                        url=f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={yt_id}&maxResults=1&order=date&type=video&key={yt_api_key}"
                        response=requests.get(url).json()
                        if not response.get('items'): continue # თუ არხს ვიდეო არ აქვს
                        latest_video = response['items'][0]; video_id = latest_video['id']['videoId']
                        last_saved_id = config.get("last_video_id")
                        if last_saved_id is None: data[guild_id][yt_id]['last_video_id'] = video_id; save_yt_data(data); continue
                        if last_saved_id != video_id:
                            video_details_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={yt_api_key}"
                            video_details_res = requests.get(video_details_url).json()
                            if video_details_res.get('items'):
                                video_details = video_details_res['items'][0]
                                if video_details['snippet'].get('liveBroadcastContent') == 'none':
                                    data[guild_id][yt_id]['last_video_id'] = video_id; save_yt_data(data)
                                    await channel.send(f"📢 **ახალი ვიდეო** {latest_video['snippet']['channelTitle']}:\nhttps://www.youtube.com/watch?v={video_id}")
                    except Exception as e: print(f"YouTube (video) error {yt_id}: {e}")

                # ლაივები
                if notify_type in ["live", "both"]:
                    try:
                        url=f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={yt_id}&eventType=live&type=video&key={yt_api_key}"
                        response = requests.get(url).json(); was_live = config.get("is_live", False)
                        if response.get('items'):
                            if not was_live:
                                live_video = response['items'][0]; video_id = live_video['id']['videoId']
                                data[guild_id][yt_id]['is_live'] = True; save_yt_data(data)
                                await channel.send(f"🔴 **ლაივია** {live_video['snippet']['channelTitle']} ლაივში შემოვიდა!\nhttps://www.youtube.com/watch?v={video_id}")
                        elif was_live: data[guild_id][yt_id]['is_live'] = False; save_yt_data(data)
                    except Exception as e: print(f"YouTube (live) error {yt_id}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(YouTubeCog(bot))
