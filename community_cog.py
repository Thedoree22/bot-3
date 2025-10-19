import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import random
from typing import Optional

WELCOME_DB = "welcome_data.json" # იგივე ფაილს ვიყენებთ Leave-სთვისაც
AUTOROLE_DB = "autorole_data.json"

def load_data(file):
    if not os.path.exists(file): return {}
    try:
        with open(file, "r", encoding='utf-8') as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return {}

def save_data(data, file):
    try:
        with open(file, "w", encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"ფაილში შენახვის შეცდომა ({file}): {e}")

class CommunityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- ტექსტის დახატვის დამხმარე ფუნქცია Shadow ეფექტით ---
    def draw_text_with_shadow(self, draw, xy, text, font, fill_color, shadow_color=(0, 0, 0, 150), shadow_offset=(2, 2)):
        x, y = xy; sx, sy = shadow_offset
        draw.text((x + sx, y + sy), text, font=font, fill=shadow_color, anchor="lt")
        draw.text(xy, text, font=font, fill=fill_color, anchor="lt")

    # --- Welcome/Leave სურათის გენერირების ფუნქცია (მწვანე ფონი) ---
    async def create_join_leave_image(self, member_name: str, guild_name: str, avatar_url: Optional[str], mode: str) -> Optional[discord.File]:
        try:
            W, H = (1000, 400) # სურათის ზომა

            # ფონი: მწვანე-შავი გრადიენტი + ვარსკვლავები
            img = Image.new("RGBA", (W, H)); draw = ImageDraw.Draw(img)
            start_color = (0, 70, 20) # მუქი მწვანე
            end_color = (0, 0, 0)     # შავი
            for i in range(H):
                ratio=i/H; r=int(start_color[0]*(1-ratio)+end_color[0]*ratio); g=int(start_color[1]*(1-ratio)+end_color[1]*ratio); b=int(start_color[2]*(1-ratio)+end_color[2]*ratio)
                draw.line([(0,i),(W,i)], fill=(r,g,b))
            star_color = (255, 255, 255, 150)
            for _ in range(100):
                x=random.randint(0,W); y=random.randint(0,H); size=random.randint(1,3)
                draw.ellipse([(x,y),(x+size,y+size)], fill=star_color)

            # ავატარი
            AVATAR_SIZE = 180; avatar_pos = (80, (H // 2) - (AVATAR_SIZE // 2))
            if avatar_url:
                try:
                    response = requests.get(avatar_url, timeout=10); response.raise_for_status()
                    avatar_image = Image.open(io.BytesIO(response.content)).convert("RGBA")
                    avatar_image = avatar_image.resize((AVATAR_SIZE, AVATAR_SIZE))
                    mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0); draw_mask = ImageDraw.Draw(mask); draw_mask.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
                    img.paste(avatar_image, avatar_pos, mask)
                except Exception as e:
                    print(f"ავატარის ჩატვირთვის შეცდომა: {e}"); draw.ellipse([avatar_pos, (avatar_pos[0]+AVATAR_SIZE, avatar_pos[1]+AVATAR_SIZE)], outline="grey", width=3)
            else: draw.ellipse([avatar_pos, (avatar_pos[0]+AVATAR_SIZE, avatar_pos[1]+AVATAR_SIZE)], outline="grey", width=3)

            # ტექსტის დამატება
            draw = ImageDraw.Draw(img)
            try:
                font_regular = ImageFont.truetype("NotoSansGeorgian-Regular.ttf", 50)
                font_bold = ImageFont.truetype("NotoSansGeorgian-Bold.ttf", 65)
                font_server = ImageFont.truetype("NotoSansGeorgian-Regular.ttf", 40)
            except IOError: print("!!! ფონტები ვერ მოიძებნა!"); return None

            text_x = avatar_pos[0] + AVATAR_SIZE + 50
            user_name = member_name
            if len(user_name) > 18: user_name = user_name[:15] + "..."
            
            # ტექსტი დამოკიდებულია იმაზე, წევრი შემოვიდა თუ გავიდა
            if mode == "join":
                line1_text = "მოგესალმებით"
                line3_text = f"{guild_name} - ში!"
                name_color = (255, 255, 255) # თეთრი
            else: # mode == "leave"
                line1_text = "დაგვტოვა"
                line3_text = f"{guild_name} - დან"
                name_color = (200, 200, 200) # ოდნავ მუქი

            # სიმაღლეების გამოთვლა
            bbox1 = font_regular.getbbox(line1_text); h1 = bbox1[3] - bbox1[1]
            bbox2 = font_bold.getbbox(user_name); h2 = bbox2[3] - bbox2[1]
            bbox3 = font_server.getbbox(line3_text); h3 = bbox3[3] - bbox3[1]
            line_spacing = 15
            total_text_height = h1 + h2 + h3 + (line_spacing * 2)
            current_y = (H // 2) - (total_text_height // 2)

            # ტექსტის დახატვა
            self.draw_text_with_shadow(draw, (text_x, current_y), line1_text, font_regular, fill_color=(220, 220, 220))
            current_y += h1 + line_spacing
            self.draw_text_with_shadow(draw, (text_x, current_y), user_name, font_bold, fill_color=name_color)
            current_y += h2 + line_spacing
            self.draw_text_with_shadow(draw, (text_x, current_y), line3_text, font_server, fill_color=(180, 180, 180))

            # სურათის შენახვა
            final_buffer = io.BytesIO(); img.save(final_buffer, "PNG"); final_buffer.seek(0)
            return discord.File(fp=final_buffer, filename=f"{mode}.png")
        except Exception as e:
            print(f"სურათის შექმნისას მოხდა შეცდომა ({mode}): {e}"); import traceback; traceback.print_exc(); return None

    # --- Setup ბრძანებები ---
    @app_commands.command(name="welcome", description="აყენებს მისალმება გაცილების არხს")
    @app_commands.describe(channel="აირჩიე არხი")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = load_data(WELCOME_DB); data[str(interaction.guild.id)] = {"channel_id": channel.id}; save_data(data, WELCOME_DB)
        await interaction.response.send_message(f"მისალმების და გაცილების არხი არის {channel.mention}", ephemeral=True)

    @app_commands.command(name="autorole", description="აყენებს როლს რომელიც ავტომატურად მიენიჭება")
    @app_commands.describe(role="აირჩიე როლი")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole_setup(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.guild.me.top_role <= role:
            await interaction.response.send_message("მე არ შემიძლია ამ როლის მინიჭება მიუთითე ჩემს როლზე დაბალი როლი", ephemeral=True); return
        data = load_data(AUTOROLE_DB); data[str(interaction.guild.id)] = {"role_id": role.id}; save_data(data, AUTOROLE_DB)
        await interaction.response.send_message(f"ავტო როლი არის **{role.name}**", ephemeral=True)

    # --- ივენთები ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        # როლის მინიჭება
        autorole_data = load_data(AUTOROLE_DB)
        if guild_id in autorole_data:
            role_id = autorole_data[guild_id].get("role_id"); role = member.guild.get_role(role_id)
            if role: try: await member.add_roles(role) except Exception as e: print(f"Error adding role: {e}")

        # მისალმების გაგზავნა
        welcome_data = load_data(WELCOME_DB)
        if guild_id in welcome_data:
            channel_id = welcome_data[guild_id].get("channel_id")
            channel = member.guild.get_channel(channel_id)
            if channel:
                welcome_file = await self.create_join_leave_image(member.name, member.guild.name, member.avatar.url if member.avatar else None, "join")
                if welcome_file: await channel.send(f"შემოგვიერთდა {member.mention} გთხოვ გაერთო", file=welcome_file)
                else: await channel.send(f"შემოგვიერთდა {member.mention} გთხოვ გაერთო")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        # გაცილების გაგზავნა
        # ვიყენებთ იგივე welcome_data-ს და არხს
        welcome_data = load_data(WELCOME_DB)
        if guild_id in welcome_data:
            channel_id = welcome_data[guild_id].get("channel_id")
            channel = member.guild.get_channel(channel_id)
            if channel:
                leave_file = await self.create_join_leave_image(member.name, member.guild.name, member.avatar.url if member.avatar else None, "leave")
                if leave_file: await channel.send(file=leave_file)
                # ტექსტს ცალკე აღარ ვაგზავნით, რადგან სურათზე წერია

async def setup(bot: commands.Bot):
    if isinstance(bot, commands.Bot): await bot.add_cog(CommunityCog(bot))
    else: print("შეცდომა: CommunityCog არასწორი bot ობიექტი")
