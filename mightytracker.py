import os
import aiohttp
import asyncio
import json
import io
from dotenv import load_dotenv
from pathlib import Path
import tempfile as tf
load_dotenv()

wynn_token = os.getenv('WYNN_TOKEN')
if wynn_token is None:
    print('ERROR: WYNN API NOT LINKED')
else:
    print('token aquired')

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
    async def get_guild_player(self, guild_pref:str):
        """
        Returns the data of all the players in a guild as a JSON
        If get_guild_player(esi), returns all members in ESI."""
        url = f"{self.url}/guild/prefix/{guild_pref}"

        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            guild_data = resp.json()
            return guild_data
guilds = ['ESI', 'ANO', 'CYAN']
async def get_guild_data(guilds):
    api = WynnAPI.get_wynn_api()
    print('Connected to Wynncraft API')
    dp = Path('/home/themightyade/Desktop/Wynnstats')
    for guild in guilds:
        try:
            data = await api.get_guild_player(guild)
            if data is None:
                print(f'ERROR: {guild} does not exist')
                continue
            with tf.NamedTemporaryFile(mode = 'w+',
                                       suffix = '.json',
                                       encoding = 'utf-8'
            ) as total_json_file:
                guild_json = json.dump(data, total_json, indent = 4)
                guild_json = guild_json.get('members')
                for i in guild_json.keys():
                    if i = 'total':
                        continue
                    for member in i:
                        path = dp / member
                
                
        except Exception as e:
            print(f"ERROR: MY CODE SUCKS. Also {type(e).__name__}: {e}")     

