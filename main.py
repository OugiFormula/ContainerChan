import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from graph import generate_gpu_graph
import json
import os
import datetime

with open('config.json') as f:
    config = json.load(f)
    print("Config Loaded!")

bot_token = config["bot_token"]

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
start_time = datetime.datetime.utcnow()

@bot.event
async def on_ready():
    print("------------------------------------")
    print("Bot Name: " + bot.user.name)
    print("Discord Version: " + discord.__version__)
    print("Bot created by Doogie Doog")
    print("------------------------------------")
    await bot.change_presence(activity=discord.Game(name='Bleh'))
    await bot.tree.sync()
    print("Commands synced!")

# Global variable to store GPU data
gpu_data = []
current_index = {}

# Function to fetch GPU data
async def fetch_gpu_data():
    url = "https://app-api.salad.com/api/v2/demand-monitor/gpu"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch GPU data: {response.status}")
                return []

# Function to create an embed for a GPU
def create_gpu_embed(gpu, index, total):
    embed = discord.Embed(
        title=f"{gpu['name']} ({index + 1}/{total})",
        color=discord.Color.blue(), timestamp=datetime.datetime.now()
    )
    embed.add_field(name="Average Earning", value=f"${gpu['earningRates']['avgEarning']:.2f}", inline=False)
    embed.add_field(name="Average Earning Time (Minutes)", value=gpu['earningRates']['avgEarningTimeMinutes'], inline=False)
    embed.add_field(name="Max Earning Rate", value=f"${gpu['earningRates']['maxEarningRate']:.2f}", inline=True)
    embed.add_field(name="Min Earning Rate", value=f"${gpu['earningRates']['minEarningRate']:.2f}", inline=True)
    embed.add_field(name="Recommended RAM (GB)", value=gpu['recommendedSpecs']['ramGb'], inline=True)
    embed.add_field(name="Utilization (%)", value=gpu['utilizationPct'], inline=True)
    embed.set_thumbnail(url="https://i.imgur.com/0pbot5n.png")
    return embed

# Command to display GPUs
@bot.tree.command(name="gpu", description="Displays GPU data in a leaderboard system")
async def gpu(interaction: discord.Interaction):
    global gpu_data
    if not gpu_data:
        gpu_data = await fetch_gpu_data()
        if not gpu_data:
            await interaction.response.send_message("Unable to fetch GPU data. Please try again later.")
            return

    user_id = interaction.user.id
    current_index[user_id] = 0
    embed = create_gpu_embed(gpu_data[current_index[user_id]], current_index[user_id], len(gpu_data))
    view = GPUView(user_id)
    await interaction.response.send_message(embed=embed, view=view)

class GPUView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global gpu_data
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your session.", ephemeral=True)
            return

        current_index[self.user_id] = (current_index[self.user_id] - 1) % len(gpu_data)
        embed = create_gpu_embed(gpu_data[current_index[self.user_id]], current_index[self.user_id], len(gpu_data))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global gpu_data
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your session.", ephemeral=True)
            return

        current_index[self.user_id] = (current_index[self.user_id] + 1) % len(gpu_data)
        embed = create_gpu_embed(gpu_data[current_index[self.user_id]], current_index[self.user_id], len(gpu_data))
        await interaction.response.edit_message(embed=embed, view=self)

# About command
@bot.tree.command(name="about", description="Displays information about the bot")
async def about(interaction: discord.Interaction):
    # Calculate uptime
    uptime = datetime.datetime.utcnow() - start_time
    uptime_str = str(uptime).split(".")[0]  # Removing microseconds

    # Bot's ping
    ping = bot.latency * 1000  # Convert to ms

    # Create the embed
    embed = discord.Embed(
        title="Container-Chan",
        description="This bot fetches and displays data from the Salad API which monitors the gpu demand on the network.\nthis bot is not affiliated with Salad.",
        color=discord.Color.green(), timestamp=datetime.datetime.now()
    )
    embed.add_field(name="Bot Version", value="1.0.0", inline=False)
    embed.add_field(name="Uptime", value=uptime_str, inline=False)
    embed.add_field(name="Ping", value=f"{ping:.2f} ms", inline=True)
    embed.set_thumbnail(url="https://i.imgur.com/O1ltr0a.jpeg")
    embed.set_image(url="https://media.tenor.com/SYvxuKcTpEUAAAAi/cat-cats.gif")
    embed.set_footer(text="Created by doogie doog", icon_url="https://i.imgur.com/96n5Juo.png")
    
    await interaction.response.send_message(embed=embed)


# Graph command to generate and display the GPU earnings graph
@bot.tree.command(name="graph", description="Displays a graph of the top 10 GPUs by earnings")
async def graph(interaction: discord.Interaction):
    # Generate the graph in memory
    img_buffer = await generate_gpu_graph()

    if img_buffer is None:
        await interaction.response.send_message("Failed to generate the graph. Please try again later.")
        return

    # Send the graph as an image
    file = discord.File(img_buffer, filename="gpu_graph.png")
    embed = discord.Embed(title="Top 10 GPUs by Average Earnings", color=discord.Color.green(),timestamp=datetime.datetime.now())
    embed.set_image(url="attachment://gpu_graph.png")
    embed.set_footer(text="Data taken from salad api, this bot isn't affiliated with salad!")
    await interaction.response.send_message(embed=embed, file=file)

# Run the bot
bot.run(bot_token)
