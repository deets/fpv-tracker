import time
import network

NETWORKS = {
    b"TP-LINK_2.4GHz_BBADE9": b"51790684",
}

def do_connect(verify=False):
    sta_if = network.WLAN(network.STA_IF)
    if verify:
        known = [item[0] for item in sta_if.scan()]

    if not sta_if.isconnected():
        sta_if.active(True)
        for ssid, password in NETWORKS.items():
            if not verify or ssid in known:
                print('connecting to network... {}'.format(ssid))
                sta_if.connect(ssid, password)
                for _ in range(10):
                    if sta_if.isconnected():
                        break
                    time.sleep(1.0)

    print('network config:', sta_if.ifconfig())


def stop():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
