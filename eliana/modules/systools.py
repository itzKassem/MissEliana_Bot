import subprocess
import time
import os
import requests
import speedtest
import json
import sys
import traceback
import psutil
import platform
import eliana.modules.helper_funcs.cas_api as cas
import eliana.modules.helper_funcs.git_api as git

from datetime import datetime
from platform import python_version, uname
from telegram import Update, Bot, Message, Chat, ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.error import BadRequest, Unauthorized

from eliana import dispatcher, OWNER_ID, SUDO_USERS
from eliana.modules.helper_funcs.filters import CustomFilters
from eliana.modules.helper_funcs.extraction import extract_text, extract_user
from eliana.modules.disable import DisableAbleCommandHandler, DisableAbleRegexHandler


def speed_convert(size):
    power = 2 ** 10
    zero = 0
    units = {0: '', 1: 'Kb/s', 2: 'Mb/s', 3: 'Gb/s', 4: 'Tb/s'}
    while size > power:
        size /= power
        zero += 1
    return f"{round(size, 2)} {units[zero]}"

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

@run_async
def status(bot: Bot, update: Update):
	message = update.effective_message
	chat = update.effective_chat
	###BOT
	stat = "--- Bot information ---\n"
	stat += "Python version: "+python_version()+"\n"
	stat += "CAS API version: "+str(cas.vercheck())+"\n"
	stat += "GitHub API version: "+str(git.vercheck())+"\n"
	##SW
	uname = platform.uname()
	softw = "--- System information ---\n"
	softw += f"OS: {uname.system}\n"
	softw += f"Version: {uname.version}\n"
	softw += f"Release: {uname.release}\n"
	##Boot Time
	boot_time_timestamp = psutil.boot_time()
	bt = datetime.fromtimestamp(boot_time_timestamp)
	softw += f"Boot Time: {bt.year}/{bt.month}/{bt.day}  {bt.hour}:{bt.minute}:{bt.second}\n"
	##CPU
	cpufreq = psutil.cpu_freq()
	cpuu = f"CPU Frequency: {cpufreq.current:.2f}Mhz\n"
	cpuu += f"CPU Usage: {psutil.cpu_percent()}%\n"
	##RAM
	svmem = psutil.virtual_memory()
	memm = f"RAM: {get_size(svmem.total)} - {svmem.percent}% used\n"
	reply = "<code>" + str(softw) + str(cpuu) + str(memm) + str(stat) + "</code>\n"
	bot.send_message(chat.id, reply, parse_mode=ParseMode.HTML)

@run_async
def get_bot_ip(bot: Bot, update: Update):
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


def ping(bot: Bot, update: Update):
    message = update.effective_message
    parsing = extract_text(message).split(' ')
    if (len(parsing) < 2):
        message.reply_text("Give me an address to ping!")
        return
    elif (len(parsing) > 2):
        message.reply_text("Too many arguments!")
        return
    dns = (parsing)[1]
    out = ""
    under = False
    if os.name == 'nt':
        try:
            output = subprocess.check_output("ping -n 1 " + dns + " | findstr time*", shell=True).decode()
        except:
            message.reply_text("There was a problem parsing the IP/Hostname")
            return
        outS = output.splitlines()
        out = outS[0]
    else:
        try:
            out = subprocess.check_output("ping -c 1 " + dns + " | grep time=", shell=True).decode()
        except:
            message.reply_text("There was a problem parsing the IP/Hostname")
            return
    splitOut = out.split(' ')
    stringtocut = ""
    for line in splitOut:
        if (line.startswith('time=') or line.startswith('time<')):
            stringtocut = line
            break
    newstra = stringtocut.split('=')
    if len(newstra) == 1:
        under = True
        newstra = stringtocut.split('<')
    newstr = ""
    if os.name == 'nt':
        newstr = newstra[1].split('ms')
    else:
        newstr = newstra[1].split(' ')  # redundant split, but to try and not break windows ping
    ping_time = float(newstr[0])
    if os.name == 'nt' and under:
        update.effective_message.reply_text(" Ping speed of " + dns + " is <{}ms".format(ping_time))
    else:
        update.effective_message.reply_text(" Ping speed of " + dns + ": {}ms".format(ping_time))
        
@run_async
def pong(bot: Bot, update: Update):
    chat = update.effective_chat
    start_time = time.time()
    test = bot.send_message(chat.id, "<code>Pong!</code>", parse_mode=ParseMode.HTML)
    end_time = time.time()
    ping_time = float(end_time - start_time)
    test.delete()
    test = bot.send_message(chat.id, "<code>Pong!\nSpeed: {0:.2f}s</code>".format(ping_time), parse_mode=ParseMode.HTML)
    time.sleep(10)
    test.delete()
    
@run_async
def log(bot: Bot, update: Update):
	chat = update.effective_chat
	message = update.effective_message
	eventdict = message.to_dict()
	jsondump = json.dumps(eventdict, indent=4)
	bot.send_message(chat.id, f"<code>"+jsondump+"</code>", parse_mode=ParseMode.HTML)

@run_async
def speedtst(bot: Bot, update: Update):
    chat = update.effective_chat
    del_msg = bot.send_message(chat.id, "<code>Running speedtest...</code>",
                               parse_mode=ParseMode.HTML)
    test = speedtest.Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    result = test.results.dict()
    del_msg.delete()
    update.effective_message.reply_text("<b>SpeedTest Results</b> \n\n"
                                        "<b>Download:</b> "
                                        f"<code>{speed_convert(result['download'])}</code> \n"
                                        "<b>Upload:</b> "
                                        f"<code>{speed_convert(result['upload'])}</code> \n"
                                        "<b>Ping:</b> "
                                        f"<code>{result['ping']}</code> \n"
                                        "<b>ISP:</b> "
                                        f"<code>{result['client']['isp']}</code>",
                                        parse_mode=ParseMode.HTML)
                                        
STATUS_HANDLER = CommandHandler("status", status, filters=CustomFilters.sudo_filter)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))
PING_HANDLER = CommandHandler("cping", ping, filters=CustomFilters.sudo_filter)
SPEED_HANDLER = CommandHandler("speed", speedtst, filters=CustomFilters.sudo_filter)
PONG_HANDLER = CommandHandler("ping", pong)
LOG_HANDLER = DisableAbleCommandHandler("log", log, filters=Filters.user(OWNER_ID))
  
dispatcher.add_handler(STATUS_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(SPEED_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(PONG_HANDLER)
dispatcher.add_handler(LOG_HANDLER)

