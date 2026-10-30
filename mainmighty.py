#### These are just the imports
#discord bots
from operator import imod
import io
import json
import aiohttp
import discord as dc
import asyncio


from discord import app_commands as cmd, Intents
import logging
from dotenv import load_dotenv
import os


#plot and data
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statistics

#fun
import random as rnd
import math

from fontTools.varLib.cff import pd_blend_fields
from numpy.core import defchararray
from pandas._testing import contexts
from urllib3.util import url, response

load_dotenv()

async def ask_tinyllama(question: str) -> str:
    """Generate a response using Tiny LLama"""

    payload = {
        "model": "tinyllama",
        "prompt": f'{question}. (Also you are MightyBot, Act Mighty in your response)',
        "stream": False,
        "options": {
            "num_predict": 200,
            "temperature": 0.7,
        },
    }

    timeout = aiohttp.ClientTimeout(total=180)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            "http://127.0.0.1:11434/api/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["response"].strip()

dc_token = os.getenv("DISCORD_TOKEN")
if dc_token is None:
    print('ERROR: DISCORD TOKEN NOT LINKED')
wynn_token = os.getenv('WYNN_TOKEN')
if wynn_token is None:
    print('ERROR: WYNN API NOT LINKED')
print(dc_token)
print(wynn_token)
handler = logging.FileHandler(
    filename="discord.log",
    encoding="utf-8",
    mode="w"
)

intents: Intents = dc.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = dc.Client(intents=intents)
tree = cmd.CommandTree(client)

api = None
url_wynn = "https://api.wynncraft.com/v3"

class WynnAPI:
    url = url_wynn
    _instance = None
    _session_lock = asyncio.Lock()
    def __init__(self,
                 session: aiohttp.ClientSession,
                 token: str = wynn_token
                 ):
        self.token = token
        self.session = session
    @property
    def closed(self):
        return self.session.closed
    @classmethod
    async def get_wynn_api(cls):
        async with cls._session_lock:
            if cls._instance is None or cls._instance.closed:
                _session = aiohttp.ClientSession()
                cls._instance = cls(_session)
            return cls._instance

    async def close(self):
        if not self.session.closed:
            await self.session.close()

    async def get_player(self, username: str):
        url = f"{self.url}/player/{username}"

        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
    async def get_guild(self, guild: str):
        url = f"{self.url}/guild/prefix/{guild}"

        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
            
    async def get_character(self, username: str, character:str):
        url = f"{self.url}/player/{username}/characters/{character}"
        
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
class MyClient(dc.Client):
    async def close(self):
        global api

        if api is not None:
            await api.close()

        await super().close()


@client.event
async def on_ready():
    global api
    api = await WynnAPI.get_wynn_api()
    print('Connected to Wynncraft API')
    await tree.sync()
    print('Mighty Bot online')
@tree.command(
    name = 'warteam',
    description = 'Gather an estimate of the guilds warteam (Sucks ass)',
)
async def warteam(interaction: dc.Interaction,guild: str):
    await interaction.response.defer()
    try:
        data = await api.get_guild(guild)
        if data is None:
            await interaction.followup.send(
                f'{guild} sucks as (Does not Exist)'
                )
            return
        o_members = []
        rank = []
        online = int(data['online'])
        data = data['members']
        for key in data:
            if key == 'total':
                continue
            for player in data[key]:
                p_data = data[key][player]
                if p_data['online'] is True:
                    o_members.append(player)
                    rank.append(key)
                    
                    
        streamers = online - len(o_members)
        max_size = 5 - streamers
        
        if max_size <= 0:
            await interaction.followup.send('Hey, The warrers are in `/stream`. \n MightyBot can not return warrers')
            return 
    
        world_v = []
        character_v = []
        for member in o_members:
            p_data = await api.get_player(member)
            if p_data is None:
                world_v.append('N/A')
            else:
                world_v.append(p_data['server'])
                character = p_data['activeCharacter']
                c_data = await api.get_character(member, character)
                if c_data is None:
                    character_v.append('N/A')
                else:
                    character_v.append(c_data['type'])
                    
        world_s = set(world_v)
        df = pd.DataFrame({ 'players' : o_members, 'world' : world_v, 'class' : character_v})
        
        counts = df['world'].value_counts()
        world_max = counts[(counts <= max_size)]
        world = world_max.idxmax()
        warteam = df[df['world'] == world].head(max_size)
            
        # Sort the world of onlime members
        
        # Take account of max members in a team and /stream
        
        # Return message containign war team
        await interaction.followup.send(f'{warteam} \n help or ban. Also {streamers} people in /stream')
    except Exception as e:
        print(f"ERROR: MY CODE SUCKS. Also {type(e).__name__}: {e}")
        await interaction.followup.send(f"ERROR: MY CODE SUCKS. Also `{type(e).__name__}: {e}`")
    
@tree.command(
    name = "stalk_guild",
    description="Gather Guild info as a JSON file",
)
async def stalk_guild(interaction: dc.Interaction,guild: str):
    await interaction.response.defer()
    try:
        data = await api.get_guild(guild)
        if data is None:
            await interaction.followup.send(
                f'`{guild}` sucks ass. (Does not exist)'
            )
            return
        json_data = json.dumps(data, indent=2)
        file = dc.File(
            io.BytesIO(json_data.encode("utf-8")),
            filename=f"{guild}.json"
        )
        await interaction.followup.send(
            content=f"We got your data now :D **{guild}**:",
            file=file
        )
    except Exception as e:
        print(f"ERROR: MY CODE SUCKS. Also {type(e).__name__}: {e}")
        await interaction.followup.send(f"ERROR: MY CODE SUCKS. Also `{type(e).__name__}: {e}`")
@tree.command(
    name="raid_bar_player",
    description="show a player's raid stats",
)
async def raid_bar_player(interaction: dc.Interaction,username: str):
    await interaction.response.defer()
    try:
        data  = await api.get_player(username)
        if data is None:
            await interaction.followup.send(
                f'{username} sucks ass (Does Not Exist).'
            )
            return
        raid_data = data.get("globalData")
        raid_data = raid_data.get("raids")
        raid_data = raid_data.get("list")
        json_data = json.dumps(raid_data, indent=2)
        file = dc.File(
        io.BytesIO(json_data.encode("utf-8")),
        filename=f"{username}.json"
    )
        await interaction.followup.send(
            content=f"We got your data now :D **{username}**:",
            file=file
    )
    except Exception as e:
        print(f"ERROR: MY CODE SUCKS. Also {type(e).__name__}: {e}")
        await interaction.followup.send(f"ERROR: MY CODE SUCKS. Also `{type(e).__name__}: {e}`")


@tree.command(
    name="stalk_player",
    description="Gather Player info as a JSON file",
)
async def stalk_player(interaction: dc.Interaction,username: str):
    await interaction.response.defer()
    try:
        data = await api.get_player(username)
        if data is None:
            await interaction.followup.send(
                f"`{username}` sucks ass (Does Not Exist)."
            )
            return
        json_data = json.dumps(data, indent=2)
        file = dc.File(
            io.BytesIO(json_data.encode("utf-8")),
            filename=f"{username}.json"
        )
        await interaction.followup.send(
            content=f"We got your data now :D **{username}**:",
            file=file
        )
    except Exception as e:
        print(f"ERROR: MY CODE SUCKS. Also {type(e).__name__}: {e}")
        await interaction.followup.send(f"ERROR: MY CODE SUCKS. Also `{type(e).__name__}: {e}`")



@tree.command(
    name="joe",
    description="who is joe?",
)
async def joe(interaction: dc.Interaction):
    await interaction.response.send_message("JOE MAMA!")
@tree.command(
    name="scatter",
    description = "scatter plot",
)
async def scatter(interaction: dc.Interaction):
    await interaction.response.send_message("Here is the plot")
@tree.command(
    name="get_api",
    description="shows what api is being getted",
)
async def get_api(interaction: dc.Interaction):
    await interaction.response.send_message(f"Here is the api: {api}")
@tree.command(
    name="roll",
    description="roll some dice",
)
async def roll(interaction: dc.Interaction, amount: cmd.Range[int, 1, 1000], dice_type: cmd.Range[int, 1, 1000], modifier: int):
    grand_result = 0
    numbers = []
    number_write = ''
    for i in range(amount):
        result = rnd.randint(1, dice_type)
        numbers.append(result)
        grand_result += result
    grand_result += modifier
    for number in numbers:
        number_write += f'{number} + '

    await interaction.response.send_message(f'{amount}d{dice_type} + {modifier} = {number_write}{modifier} = {grand_result}' +'\n'
    'that seems like a roll')
@tree.command(
    name="ask",
    description="Ask MightyBot a question",
)
async def ask(interaction: dc.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    try:
        answer = await ask_tinyllama(question)

        if not answer:
            answer = "Your prompt crashed my pi."

        await interaction.followup.send(
            answer[:1900],
            allowed_mentions=dc.AllowedMentions.none(),
        )

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"TMy code ass. Also: {type(e).__name__}: {e}")

        await interaction.followup.send(
          f"TMy code ass. Also: {type(e).__name__}: {e}"
        )

    except Exception as e:
        print(f"TinyLlama error: {type(e).__name__}: {e}")

        await interaction.followup.send(
            f"TMy code ass. Also: {type(e).__name__}: {e}"
        )

async def main():
    try:
        await client.start(dc_token)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
