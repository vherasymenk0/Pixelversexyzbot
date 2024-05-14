import asyncio
from random import randint
from urllib.parse import unquote

import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName

from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from .bot_info import bot_info


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.http_client = None

    async def get_tg_web_data(self, proxy: str | None) -> str:
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
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            bot = await self.tg_client.resolve_peer(bot_info['peer'])
            app = InputBotAppShortName(bot_id=bot, short_name=bot_info['short_name'])
            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=bot,
                app=app,
                platform='android',
                write_allowed=True
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(
                    string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self):
        try:
            res = await self.http_client.get(url='https://api-clicker.pixelverse.xyz/api/users')
            res.raise_for_status()

            data = await res.json()
            return data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Profile Data: {error}")
            await asyncio.sleep(delay=3)

    async def send_taps(self, taps: int):
        try:
            res = await self.http_client.post(url='https://api-clicker.pixelverse.xyz/api/users',
                                              json={'clicksAmount': str(taps)})
            res.raise_for_status()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Profile Data: {error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, proxy: str) -> None:
        try:
            response = await self.http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None, agent) -> None:
        active_turbo = False
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        clientHeaders = {
            **headers,
            **agent
        }

        async with aiohttp.ClientSession(headers=clientHeaders, connector=proxy_conn) as http_client:
            self.http_client = http_client
            if proxy:
                await self.check_proxy(proxy=proxy)

            while True:
                try:
                    profile_data = await self.get_profile_data()
                    click_count = profile_data["clicksCount"]
                    profile_id = profile_data["id"]
                    pet_id = profile_data["pet"]["id"]
                    pet_energy = profile_data["pet"]["energy"]
                    pet_level = profile_data["pet"]["level"]
                    logger.info(f"{self.session_name} | Level:{pet_level} | Clicks:{click_count} | Energy:{pet_energy}")

                    if pet_energy > settings.MIN_AVAILABLE_ENERGY:
                        taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])
                        await self.send_taps(taps)
                        await asyncio.sleep(1)

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                    if active_turbo is True:
                        active_turbo = False

                    logger.info(f"Sleep {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None, agent):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy, agent=agent)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
