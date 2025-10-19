import discord
from discord.ext import commands
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if BOT_TOKEN is None:
    print("ფატალური შეცდომა: BOT_TOKEN არ არის Railway-ს ცვლადებში.")
    exit()

# --- ბოტის უფლებები (Intents) ---
# დავიწყოთ მინიმალური უფლებებით. შეგვიძლია მოგვიანებით დავამატოთ, თუ საჭირო იქნება.
intents = discord.Intents.default()
# intents.members = True # ჩართე, თუ Welcome/AutoRole დაგჭირდება
# intents.message_content = True # ჩართე, თუ შეტყობინებების წაკითხვა დაგჭირდება

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ბოტი ჩაირთო როგორც {bot.user}")
    print("-" * 30)

    # --- აქ დავამატებთ ფუნქციების (Cogs) ჩატვირთვას, როცა გვეცოდინება, რა ფუნქციები გვინდა ---
    # cogs_to_load = ['some_cog']
    # for cog in cogs_to_load:
    #     try:
    #         await bot.load_extension(cog)
    #         print(f"წარმატებით ჩაიტვირთა: {cog}")
    #     except Exception as e:
    #         print(f"შეცდომა: ვერ ჩაიტვირთა {cog}: {e}")
    # print("-" * 30)

    # --- სლეშ ბრძანებების რეგისტრაცია ---
    try:
        # თავიდან sync() არ გვჭირდება, რადგან ბრძანებები არ გვაქვს
        # synced = await bot.tree.sync()
        # print(f"წარმატებით დარეგისტრირდა {len(synced)} ბრძანება.")
        print("ბრძანებების რეგისტრაცია გამოტოვებულია (ჯერ ბრძანებები არ არის).")
    except Exception as e:
        print(f"შეცდომა ბრძანებების რეგისტრაციისას: {e}")
    
    print("-" * 30)

# ეს არის მარტივი სატესტო ბრძანება
@bot.tree.command(name="ping", description="ამოწმებს ბოტის პასუხის დროს")
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000 # მილიწამებში
    await interaction.response.send_message(f"პონგ! {latency:.2f}ms")

bot.run(BOT_TOKEN)
