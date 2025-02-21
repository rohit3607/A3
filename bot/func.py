
import json

import os
import subprocess
import math
import re
from bot import bot, bot_loop, Var, ani_cache
from pathlib import Path

import aiofiles
import aiohttp

import binascii
import base64
import re
import asyncio
from pyrogram import filters, Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait
from shortzy import Shortzy
import requests
import time
from datetime import datetime
import random
import string
from bot.core.database import db
from bot.core.database import *
from bot.core.auto_animes import get_animes
from bot.core.reporter import rep
#=============================================================================================================================================================================
# -------------------- HELPER FUNCTIONS FOR USER VERIFICATION IN DIFFERENT CASES -------------------- 
#=============================================================================================================================================================================


#from dotenv import load_dotenv
#import os

#load_dotenv()  # Load environment variables #from .env

#OWNER_ID = os.getenv("ADMINS")

OK = {}


async def genss(file):
    process = subprocess.Popen(
        ["mediainfo", file, "--Output=JSON"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, stderr = process.communicate()
    out = stdout.decode().strip()
    z = json.loads(out)
    p = z["media"]["track"][0]["Duration"]
    return int(p.split(".")[-2])


async def duration_s(file):
    tsec = await genss(file)
    x = round(tsec / 5)
    y = round(tsec / 5 + 30)
    pin = convertTime(x)
    if y < tsec:
        pon = convertTime(y)
    else:
        pon = convertTime(tsec)
    return pin, pon


async def gen_ss_sam(hash, filename, log):
    try:
        ss_path, sp_path = None, None
        os.mkdir(hash)
        tsec = await genss(filename)
        fps = 10 / tsec
        ncmd = f"ffmpeg -i '{filename}' -vf fps={fps} -vframes 10 '{hash}/pic%01d.png'"
        process = await asyncio.create_subprocess_shell(
            ncmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        ss, dd = await duration_s(filename)
        __ = filename.split(".mkv")[-2]
        out = __ + "_sample.mkv"
        _ncmd = f'ffmpeg -i """{filename}""" -preset ultrafast -ss {ss} -to {dd} -c:v copy -crf 27 -map 0:v -c:a aac -map 0:a -c:s copy -map 0:s? """{out}""" -y'
        process = await asyncio.create_subprocess_shell(
            _ncmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        er = stderr.decode().strip()
        try:
            if er:
                if not os.path.exists(out) or os.path.getsize(out) == 0:
                    log.error(str(er))
                    return (ss_path, sp_path)
        except Exception:
            print(e)
        return hash, out
    except Exception as err:
        log.error(str(err))

# Check user subscription in channels in a more optimized way
async def is_subscribed(filter, client, update):
    channel_ids = await db.get_all_channels()

    if not channel_ids:
        return True  # No forced subscription required

    user_id = update.from_user.id

    # Allow owner and admins to bypass subscription check
    if user_id == user_id in Var.ADMINS:
        return True

    # Handle the case for a single channel directly
    if len(channel_ids) == 1:
        return await is_userJoin(client, user_id, channel_ids[0])

    # Use asyncio.gather to check multiple channels concurrently
    tasks = [is_userJoin(client, user_id, channel_id) for channel_id in channel_ids if channel_id]
    results = await asyncio.gather(*tasks)

    # Return True only if the user is subscribed to ALL required channels
    return all(results)



#Chcek user subscription by specifying channel id and user id
async def is_userJoin(client, user_id, channel_id):
    #REQFSUB = await db.get_request_forcesub()
    try:
        member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}

    except UserNotParticipant:
        if await db.get_request_forcesub(): #and await privateChannel(client, channel_id):
                return await db.reqSent_user_exist(channel_id, user_id)

        return False

    except Exception as e:
        print(f"!Error on is_userJoin(): {e}")
        return False

#=============================================================================================================================================================================#

#subscribed = filters.create(is_subscribed)
