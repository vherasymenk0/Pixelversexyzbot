import asyncio
from random import randint
import hashlib
import hmac
import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
import math
from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from .bot_info import bot_info

api_url = bot_info['api']


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.http_client = None

    async def get_tg_id(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            me = await self.tg_client.get_me()
            await self.tg_client.disconnect()

            return str(me.id)

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self):
        try:
            res = await self.http_client.get(url=f'{api_url}/users')
            res.raise_for_status()
            data = await res.json()
            return data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting profile data: {error}")
            await asyncio.sleep(delay=3)

    async def send_taps(self, taps: int):
        try:
            res = await self.http_client.post(url=f'{api_url}/users', json={'clicksAmount': taps})
            res.raise_for_status()
            data = await res.json()
            return data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while send taps: {error}")
            await asyncio.sleep(delay=3)

    async def level_up(self, pet_id: int):
        try:
            res = await self.http_client.post(url=f'{api_url}/pets/user-pets/{pet_id}/level-up')
            res.raise_for_status()
            data = await res.json()
            return data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while pets level up: {error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, proxy: str) -> None:
        try:
            response = await self.http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def create_secret_hash(self, my_id: str) -> str:
        try:
            secret_hash = hmac.new(settings.SECRET_KEY.encode("utf-8"), my_id.encode("utf-8"), hashlib.sha256).hexdigest()

            return secret_hash
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while creating secret hash {error}")

    async def run(self, proxy: str | None, agent) -> None:
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        my_id = await self.get_tg_id(proxy)
        secret = await self.create_secret_hash(my_id)

        clientHeaders = {
            **headers,
            **agent,
            'Tg-Id': my_id,
            'Secret': secret
        }

        async with aiohttp.ClientSession(headers=clientHeaders, connector=proxy_conn) as http_client:
            self.http_client = http_client
            if proxy:
                await self.check_proxy(proxy=proxy)

            while True:
                try:
                    profile_data = await self.get_profile_data()
                    click_count = math.floor(profile_data["clicksCount"])
                    pet_energy = profile_data["pet"]["energy"]
                    pet_level = profile_data["pet"]["level"]
                    logger.info(f"{self.session_name} | Level:{pet_level} | Clicks:{click_count} | Energy:{pet_energy}")

                    if pet_energy > settings.MIN_AVAILABLE_ENERGY:
                        taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])
                        profile_data = await self.send_taps(taps)

                        points_tapped = math.floor(taps * profile_data["pointPerClick"])
                        balance = math.floor(profile_data['clicksCount'])
                        logger.success(
                            f"{self.session_name} | Successful tapped +{points_tapped} | Balance: ~{balance} | Energy: {profile_data['pet']['energy']}")
                        await asyncio.sleep(1)
                    else:
                        energy_per_second = profile_data['pet']['energyPerSecond']
                        max_energy = profile_data['pet']['maxEnergy']
                        current_energy = profile_data['pet']['energy']
                        sleep_time = math.ceil((max_energy - current_energy) / energy_per_second)

                        logger.info(f"{self.session_name} | Reached minimum energy, sleep {sleep_time}s for full energy recovery ")
                        await asyncio.sleep(sleep_time)
                        continue

                    if settings.AUTO_UPGRADE:
                        balance = math.floor(profile_data["clicksCount"])
                        upgrade_price = math.floor(profile_data["pet"]["levelUpPrice"])
                        if balance >= upgrade_price:
                            level_data = await self.level_up(profile_data["pet"]['id'])
                            logger.info(f"{self.session_name} | Successfully upgraded to {level_data['level']} lvl")
                            await asyncio.sleep(1)
                            continue

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                    logger.info(f"Sleep between taps {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None, agent):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy, agent=agent)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
