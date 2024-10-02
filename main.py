import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
from typing import Literal
import random
import asyncio
from datetime import datetime, timedelta
from art import text2art  
from colorama import Fore, Style, init

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
BOT_ID = int(os.getenv("BOT_ID"))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)

role_file = "role.json"
member_file = "member.json"

def read_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        return {}

def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

roles_data = read_json(role_file)
members_data = read_json(member_file)

def check_guild_and_bot(interaction):
    return interaction.guild and interaction.guild.id == GUILD_ID and client.user.id == BOT_ID

@client.event
async def on_application_command_error(interaction: discord.Interaction, error: Exception):
    print(f"An error occurred: {error}")

@client.event
async def on_ready():
    try:
        # Create ASCII Art text for "Skode Studio"
        ascii_art_text = text2art("Skode Studio")

        # Print the ASCII Art text in the console with light color
        print(Fore.LIGHTCYAN_EX + ascii_art_text + Style.RESET_ALL)
        print(Fore.LIGHTGREEN_EX + f"Logged in as {client.user}" + Style.RESET_ALL)

        # Change bot presence
        await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.listening, name="Skode®Studio"))

        # Synchronize the commands with Discord for the specified guild
        guild = discord.Object(id=GUILD_ID)
        await client.tree.sync(guild=guild)
        print(Fore.LIGHTGREEN_EX + "Commands synchronized successfully." + Style.RESET_ALL)
        
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Error in on_ready event: {e}" + Style.RESET_ALL)

@client.tree.command(name="role", description="لإضافة الرتبة التي سيسمح لها باستخدام البوت", guild=discord.Object(id=GUILD_ID))
async def role_member(interaction: discord.Interaction, الرتبة: discord.Role, الوظيفة: Literal["اضافة", "ازالة"]):
    user = interaction.user
    owner = interaction.guild.owner_id

    try:
        if user.id == owner:
            if الوظيفة == "اضافة":
                if "give_role" not in roles_data:
                    roles_data["give_role"] = []

                if الرتبة.id not in [role['role_id'] for role in roles_data["give_role"]]:
                    roles_data["give_role"].append({"role_id": الرتبة.id})
                    write_json(role_file, roles_data)
                    await interaction.response.send_message(f"Rank added {الرتبة.mention} For database", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Rank {الرتبة.mention} already exists", ephemeral=True)
            elif الوظيفة == "ازالة":
                roles_data["give_role"] = [role for role in roles_data.get("give_role", []) if role['role_id'] != الرتبة.id]
                write_json(role_file, roles_data)
                await interaction.response.send_message(f"The rank has been removed. {الرتبة.mention} From the database", ephemeral=True)
        else:
            await interaction.response.send_message("Sorry, only the server owner can use this command.", ephemeral=True)
    except Exception as e:
        print(e)
        await interaction.response.send_message("There seems to be an error, make sure you entered everything correctly.", ephemeral=True)

@client.tree.command(name="giveaway", description="Start a giveaway", guild=discord.Object(id=GUILD_ID))
async def giveaway(interaction: discord.Interaction, prize: str, description: str, duration: int, duration_type: Literal["seconds", "minutes", "hours", "days"], winners_count: int):
    role_ids = [role['role_id'] for role in roles_data.get('give_role', [])]

    try:
        user_roles = [interaction.guild.get_role(role_id) for role_id in role_ids]
        if any(role in interaction.user.roles for role in user_roles):
            if winners_count >= 1:
                user = interaction.user
                members = []

                button = discord.ui.Button(label="🎉 Join", style=discord.ButtonStyle.primary)

                server_icon_url = interaction.guild.icon.url if interaction.guild.icon else None

                now = datetime.utcnow()
                if duration_type == "seconds":
                    times = timedelta(seconds=duration)
                elif duration_type == "minutes":
                    times = timedelta(minutes=duration)
                elif duration_type == "hours":
                    times = timedelta(hours=duration)
                elif duration_type == "days":
                    times = timedelta(days=duration)
                end_time = now + times
                end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")

                embed = discord.Embed(
                    title="Giveaway 🎉",
                    description=f"{description}",
                    color=discord.Colour.gold()
                )

                if server_icon_url:
                    embed.set_thumbnail(url=server_icon_url)

                embed.add_field(name="🎁 Prize", value=prize, inline=True)
                embed.add_field(name="🏆 Winners", value="No winners yet", inline=True)  # This line should be added only once
                embed.add_field(name="😎 Host", value=user.mention, inline=True)
                embed.add_field(name="⏳ Duration", value=f"{duration} {duration_type}", inline=True)
                embed.set_footer(text=f"Ends at: {end_time_str}")

                view = discord.ui.View()
                view.add_item(button)

                async def button_callback(interaction: discord.Interaction):
                    if interaction.user not in members:
                        members.append(interaction.user)
                        if "members" not in members_data:
                            members_data["members"] = []
                        members_data["members"].append({"members_id": interaction.user.id})
                        write_json(member_file, members_data)
                        await interaction.response.send_message(f"You've joined the giveaway, {interaction.user.mention}", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"You've already joined the giveaway, {interaction.user.mention}", ephemeral=True)

                button.callback = button_callback
                await interaction.response.send_message(embed=embed, view=view)

                await asyncio.sleep(times.total_seconds())

                if members:
                    winners = random.sample(members, k=min(winners_count, len(members)))
                    winners_mention = " ".join([w.mention for w in winners])
                    embed.set_field_at(1, name="🏆 Winners", value=winners_mention, inline=True)  
                    embed.add_field(name="Number of Participants", value=len(members), inline=True)
                    message = await interaction.followup.send(f"{winners_mention} won the giveaway for {prize}")

                    # Update win date
                    for winner in winners:
                        for member_data in members_data.get('members', []):
                            if member_data['members_id'] == winner.id:
                                member_data['win_date'] = now.strftime('%Y-%m-%d %H:%M:%S UTC')
                                break
                    write_json(member_file, members_data)

                    await message.add_reaction("🎉")
                else:
                    embed.set_field_at(1, name="🏆 Winners", value="No winners", inline=True)  
                    await interaction.followup.send("No winners")

                button.disabled = True
                view.remove_item(button)
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                await interaction.response.send_message("You cannot set less than 1 winner", ephemeral=True)
        else:
            await interaction.response.send_message("Sorry, you don't have permission to use this command", ephemeral=True)
    except Exception as e:
        print(e)
        if not interaction.response.is_done():
            await interaction.response.send_message("An error occurred, please check if everything is correct", ephemeral=True)

@client.tree.command(name="member", description="To view participants in the latest giveaway", guild=discord.Object(id=GUILD_ID))
async def member_join(interaction: discord.Interaction):
    owner = interaction.guild.owner_id
    try:
        role_ids = [role['role_id'] for role in roles_data.get('give_role', [])]
        role = None
        for role_id in role_ids:
            role = interaction.guild.get_role(role_id)

        if role and role in interaction.user.roles:
            members = members_data.get('members', [])
            
            count_embed = discord.Embed(
                title="Participants",
                color=discord.Colour.green()
            )

            if len(members) > 0:
                for key, member_data in enumerate(members):
                    member_id = member_data.get('members_id')
                    win_date = member_data.get('win_date', 'N/A') 
                    member = interaction.guild.get_member(member_id)
                    if member:
                        count_embed.add_field(
                            name=f"Participant {key + 1}",
                            value=f"{member.mention}  {win_date}",
                            inline=False
                        )
            else:
                count_embed.add_field(
                    name="Participants",
                    value="No participants found",
                    inline=False
                )

            await interaction.response.send_message(embed=count_embed, ephemeral=True)
        else:
            await interaction.response.send_message("Sorry, but you do not have permission to use this command.", ephemeral=True)
    except Exception as e:
        print(e)
        if interaction.user.id == owner:
            await interaction.response.send_message("An error occurred, please ensure you have added the role that will use the bot.", ephemeral=True)
        elif role and role in interaction.user.roles:
            await interaction.response.send_message("Sorry, but you cannot use this command at the moment.", ephemeral=True)
        else:
            await interaction.response.send_message("Sorry, but you do not have permission to use this command.", ephemeral=True)
            
client.run(BOT_TOKEN)
