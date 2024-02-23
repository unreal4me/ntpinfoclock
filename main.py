import time, ntptime
from display import display
from wifi_helper import connected, get_ip_address
from machine import Timer
import json
import uasyncio as asyncio
import uaiohttpclient as aiohttp


days = ['' 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

(year,month,day,hour,minute,second,weekday,dayofyear) = time.localtime()

CONF_FILE='conf.json'
CONFIG = {}

info = {}

def connect_wifi():
    from wifi_helper import connect as connect_wifi, connected, get_ip_address
    retry_count = 0
    display.message('Wifi '+str(retry_count), delay=0.1)
    while (retry_count < CONFIG["SSID_RETRY"]):
        ip_address = connect_wifi(CONFIG["SSID"], CONFIG["SSID_PASS"], timeout_seconds=10)
        if ip_address and connected():
            return connected()
        else:
            retry_count += 1
    display.message('Wifi err', delay=0.1)
    return False

def boot_up():
    from display import display
    display.message('boot', delay=0.1)
    global CONFIG
    import os, json
    try:
        file_stat = os.stat(CONF_FILE)
    except Exception as e:
        if e.errno in (errno.ENOENT,):
            display.message('ap mode')
            print('no file - ap mode')
            return None
    try:
        with open(CONF_FILE) as conf:
            CONFIG = json.load(conf)
            print(CONFIG)
            conf.close()
    except Exception as e:
        display.message('conf err')
        print('CONF_FILE', e)
        return None
    
    if CONFIG["MACHINE_RESETS"] >= 3:
        display.message('ap mode')
        try:
            with open(CONF_FILE, "w") as conf:
                CONFIG["MACHINE_RESETS"]=0
                json.dump(CONFIG, conf)
                conf.close()
            print('3 resets - ap mode')
            return None
        except Exception as e:
            display.message('HELP')
            print('CONF_FILE save', e)
            
    online() if connect_wifi() else machine_reset()

def online():
    display.message('Online', delay=0.1)
    ntp_update()
    update_time()
    asyncio.run(get_moon(CONFIG["INFO"]["MOON_DATA_URL"]))
    #update_time_timer = Timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t:update_time())
    asyncio.run(main_loop()) #main loop

ntp_timer = Timer()
def ntp_update(period_seconds=60):
    #display.message('ntp init', delay=0.1)
    ntp_timer.deinit()
    try:
        ntptime.host = "pool.ntp.org"
        ntptime.timeout = 5
        ntptime.settime()
        display.message('ntp sync', delay=0.1)
    except Exception as e:
        if e.errno in (errno.ETIMEDOUT,):
            display.message('ntp err TIMEDOUT', delay=0.1)
            print('ntp', e)
        print('ntp err', e, e.errno)
        ntp_timer.init(period=period_seconds*1000, mode=Timer.ONE_SHOT, callback=lambda t:ntp_update())

def display_day():
    #new_day = 'Day {}'.format(dayofyear)
    #display.message('{:{}}'.format(new_day, 8+len(new_day)))
    display.message('Day {:<{}}'.format(dayofyear, 8+len(str(dayofyear))))
    
def display_date():
    display.message('{} {} {} {}'.format(days[weekday], day, months[month], year)+'{:{}}'.format(' ', 4))
    
def display_time():
    display.text('{:02d}{:02d}{:02d}'.format(hour,minute,second))

display_subs_timer = Timer()
def display_subs(subs):
    display.message('{:{}}{}'.format('subs', 8-len(subs), subs))




async def get_subs(url):
    try:
        resp = await aiohttp.request("GET", url)
        _bin_resp = await resp.read()
        counter = _bin_resp.decode()
        try:
            _ = info['subs']
        except KeyError:
            info['subs'] = 0
        display_subs_timer.init(mode=Timer.ONE_SHOT, period=1000, callback=lambda t:display_subs_counter(info['subs'], int(counter)))
    except Exception as e:
        print('get_subs: ', e)

async def get_moon(url):
    try:
        resp = await aiohttp.request("GET", url)
        _bin_resp = await resp.read()
        moon = _bin_resp.decode()
        #print(moon, type(moon))
        info['moon'] = json.loads(moon)
        #display_subs_timer.init(mode=Timer.ONE_SHOT, period=1000, callback=lambda t:display_subs_counter(subs, int(counter)))
    except Exception as e:
        print('get_moon: ', e)

def display_moon():
    try:
        display._buffer[7] = info['moon']['seven_seg']
        display.flush()
    except KeyError:
        info['moon'] = { "seven_seg" : 0 }


def display_subs_counter(old, new):
    global info
    if new == old:
        return old
    if new > old:
        _list = list(range(old, new+1))
        _delay = 1/(new-old)
    if new < old:
        _list = list(range(new, old+1))
        _list.reverse()
        _delay = 1/(old-new)
    display.message('{:{}}{}'.format('sub', 8-len(str(old)), old), delay=0.1)
    for i in _list:
        time.sleep(_delay)
        display.text('{:{}}{}'.format('sub', 8-len(str(i)), i))
    time.sleep(0.5)
    info['subs'] = new

def update_time():
    global year,month,day,hour,minute,second,weekday,dayofyear
    (year,month,day,hour,minute,second,weekday,dayofyear) = time.localtime(time.time()+3600*2)

machine_reset_timer = Timer()
def machine_reset():
    CONFIG["MACHINE_RESETS"] += 1
    display.message('reboot '+str(CONFIG["MACHINE_RESETS"]))
    try:
        with open(CONF_FILE, "w") as conf:
            json.dump(CONFIG, conf)
            conf.close()
            machine.reset()
    except Exception as e:
        display.message('HELP')
        print('CONF_FILE save', e)

#main loop
main_loop_timer = Timer()
async def main_loop():
    main_loop_timer.deinit()
    global year,month,day,hour,minute,second,weekday,dayofyear
    update_time()
    display_time()
    display_moon()
    
    if second == 0:
        asyncio.run(get_subs(CONFIG["INFO"]["COUNTER_URL"]))
    if hour == 0 and minute == 0 and second == 1:
        display_day()
    if second == 30:
        display_date()
    if minute == 0 and second == 5:
        ntp_update() if connected() else display.message('offline')
        asyncio.run(get_moon(CONFIG["INFO"]["MOON_DATA_URL"]))

    main_loop_timer.init(period=500, mode=Timer.ONE_SHOT, callback=lambda t:asyncio.run(main_loop()))

boot_up()

