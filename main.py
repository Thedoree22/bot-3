import discord
from discord.ext import commands
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if BOT_TOKEN is None:
    print("ფატალური შეცდომა: BOT_TOKEN არ არის Railway-ს ცვლადებში.")
    exit()

# --- ბოტის უფლებები (Intents) ---
intents = discord.Intents.default()
intents.members = True       # აუცილებელია Welcome, Leave, Auto-Role-ისთვის
intents.message_content = True # დავტოვოთ ყოველი შემთხვევისთვის

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ბოტი ჩაირთო როგორც {bot.user}")
    print("-" * 30)

    # --- ყველა ფუნქციის (Cogs) ჩატვირთვა ---
    cogs_to_load = [
        'community_cog',      # Welcome, Leave, Auto-Role (ახალი დიზაინით)
        'youtube_cog',        # YouTube შეტყობინებები
        'tiktok_cog'          # TikTok შეტყობინებები
    ]

    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            print(f"წარმატებით ჩაიტვირთა: {cog}")
        except Exception as e:
            print(f"შეცდომა: ვერ ჩაიტვირთა {cog}: {e}")

    print("-" * 30)

    # --- სლეშ ბრძანებების რეგისტრაცია ---
    try:
        synced = await bot.tree.sync()
        print(f"წარმატებით დარეგისტრირდა {len(synced)} ბრძანება.")
    except Exception as e:
        print(f"შეცდომა ბრძანებების რეგისტრაციისას: {e}")

    print("-" * 30)

bot.run(BOT_TOKEN)
