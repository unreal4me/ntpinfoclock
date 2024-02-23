from display import display

def get_ip_address():
  import network
  try:
    return network.WLAN(network.STA_IF).ifconfig()[0]
  except:
    return None

def connected():
  import network, time
  wlan = network.WLAN(network.STA_IF)
  return wlan.isconnected()

def connect(ssid, password, timeout_seconds=10):
    import network, time

    statuses = {
        network.STAT_IDLE: "idle",
        network.STAT_CONNECTING: "connecting to wifi........",
        2: "NOIP",
        network.STAT_GOT_IP: "got ip address",
        network.STAT_WRONG_PASSWORD: "wrong password",
        network.STAT_NO_AP_FOUND: "access point not found",
        network.STAT_CONNECT_FAIL: "failed"
    }

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)    
    wlan.connect(ssid, password)
    start = time.ticks_ms()
    status = wlan.status()

    while not wlan.isconnected() and (time.ticks_ms() - start) < (timeout_seconds * 1000):
        new_status = wlan.status()
        if status != new_status:
            status = new_status
            #display.message(statuses[status], delay=0.1)

    if wlan.status() == network.STAT_GOT_IP:
        #display.message(get_ip_address(), delay=0.1)
        return get_ip_address()
    return None