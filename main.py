import platform
import os
import socket
import logging
import sys
import getopt
import subprocess
import re

from time import sleep
from datetime import datetime as dt
from datetime import timedelta

from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

from config import *


logging.basicConfig(filename=f".{os.sep}connection.log", encoding="utf-8", level=logging.INFO)

V="0.3"
shortopts = '''hcHilvVd:C:m:''' #if after the letter there is ':' the argument is required
longopts = ["help", "chromium", "headless", "noimage", "nolocation", "verbose", "version", "hard_c=", "down=", "mac_address="] #if after name variable there is '=' the argument is required

with subprocess.Popen(["whoami"], stdout=subprocess.PIPE) as proc:
    whoami = proc.stdout.readline()
WHOAMI = whoami.decode().strip()
STARTED = dt.now()

#TODO: IMPORTANTE! Trasformare tutto questo codice con OOP in una classe in modo da avere variabili "globali" per il reboot



def help():
    print(f"""LazioDisco wifi {V}
(C) 2022-2023 Simone Flavio Paris.
Released under Apache License 2.0
    -h --help               Print this help screen.
    -c --chromium           Use chromium browser instead of Chrome.
    -H --headless           Use this script in headless mode.
    -i --noimage            Reduce bandwidth waste disabling image loading.
    -l --nolocation         Don't allow sites to track your physical location.
    -d --down               Take a integer in input, 0 for False and 1 for True.
    -C --hard_c             Take a integer in input, internal use only.
    -m --mac_address        Take a integer in input, the index of MACs list.
    -v --verbose            Print to screen all messages.
    -V --version            Print version info.
    """)

def version():
    print(f"auto DiscoLogin {V}")



def lan_sharing(power: bool):
    if power:
        try:
            with subprocess.Popen(["sudo", "-S", "wg-quick", "up", "fr0"], stdin=subprocess.PIPE) as proc:
                sleep(0.2)
                proc.communicate(f"{sudo_pwd}\n".encode())
                print()
            sleep(1)
        except Exception:
            pass
        with subprocess.Popen(["sudo", "-S", "ip", "link", "set", eth0, "up"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(1)
        subprocess.Popen(["sudo", "ifconfig", eth0, "up"])
        sleep(1)

        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        logging.info(f"\t{t_now}\tWireguard and {eth0} turned ON!")

    else:
        with subprocess.Popen(["sudo", "-S", "ifconfig", eth0, "down"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(1)
        subprocess.Popen(["sudo", "ip", "link", "set", eth0, "down"])
        sleep(1)
        try:
            subprocess.Popen(["sudo", "wg-quick", "down", "fr0"])
            print()
            sleep(1)
        except Exception:
            pass

        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        logging.info(f"\t{t_now}\t{eth0} and Wireguard turned OFF!")



def reboot(force=False, verbose=False):
    lan_sharing(0)
    t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
    if verbose:
        print(f"\n\t{t_now}\t[i] Rebooting")
    logging.error(f"\t{t_now}\t[i] Rebooting\n")
    if force:
        with subprocess.Popen(["sudo", "-S", "shutdown", "-r", "now"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
    else:
        with subprocess.Popen(["sudo", "-S", "shutdown", "-r"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())



def restart(down, mac, hard_c):
    t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
    logging.info(f"\t{t_now}\t/home/{WHOAMI}/lazio-disco_login/restart.sh {down} {mac} {hard_c}")
    subprocess.run([f"/home/{WHOAMI}/lazio-disco_login/restart.sh", str(down), str(mac), str(hard_c)])
    sys.exit("[i] Restarting")



def getDriver(chromium: bool, headless: bool, noimage: bool, nolocation: bool, verbose: bool):
    locale = "en"
    chrome_options = Options()
    chrome_options.add_argument(f"--lang={locale}")
    chrome_options.add_argument("start-maximized")
    #if chromium:
    #    chrome_options.binary_location = "/snap/bin/chromium"
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
    chrome_prefs = {}
    #chrome_prefs["profile.managed_default_content_settings"] = {"javascript": 2}
    if noimage:
        chrome_prefs["profile.default_content_settings"] = {"images": 2}
        chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
    if nolocation:
        chrome_prefs["profile.default_content_settings"] = {"location": 2}
        chrome_prefs["profile.managed_default_content_settings"] = {"location": 2}
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    #chrome_options.add_argument("user-data-dir=selenium")
    chrome_options.add_argument("disable-features=PreloadMediaEngagementData")
    chrome_options.add_argument("MediaEngagementBypassAutoplayPolicies")
    #chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--incognito")

    if not ("raspi" in platform.platform().lower() or "aarch" in platform.platform().lower()):
        if "linux" in platform.platform().lower():
            if chromium:
                try:
                    path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                    with subprocess.Popen(["sudo", "-S", "cp", "-p", f"{path}", "/usr/lib/chromedriver/"], stdin=subprocess.PIPE) as proc:
                        sleep(0.2)
                        proc.communicate(f"{sudo_pwd}\n".encode())
                except Exception:
                    path = b"/usr/lib/chromedriver/chromedriver"
            else:
                try:
                    path = ChromeDriverManager().install()
                    with subprocess.Popen(["sudo", "-S", "cp", "-p", f"{path}", "/usr/lib/chromedriver/"], stdin=subprocess.PIPE) as proc:
                        sleep(0.2)
                        proc.communicate(f"{sudo_pwd}\n".encode())
                except Exception:
                    path = b"/usr/lib/chromedriver/chromedriver"
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")

        else: #TODO: see what is platform.platform() under windows
            if chromium:
                try:
                    path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                except Exception:
                    #TODO: path for windows
                    sys.exit("[!] chromedriver not found!")
            else:
                try:
                    path = ChromeDriverManager().install()
                    with subprocess.Popen(["sudo", "-S", "cp", "-p", f"{path}", "/usr/lib/chromedriver/"], stdin=subprocess.PIPE) as proc:
                        sleep(0.2)
                        proc.communicate(f"{sudo_pwd}\n".encode())
                except Exception:
                    #TODO: path for windows
                    sys.exit("[!] chromedriver not found!")
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")

        if verbose:
            print(f"\t{t_now}\tBrowser driver path: {path}")
        logging.info(f"\t{t_now}\tBrowser driver path: {path}")

        driver = webdriver.Chrome(service=Service(path), options=chrome_options)
    else:   # If under arm, raspi or aarch
        # you have to download the right driver and put here the path
        driver = webdriver.Chrome(service=Service(b"/usr/lib/chromedriver/chromedriver"), options=chrome_options)
    
    return driver



def is_connected(prev=None, verbose=False):
    t_start = dt.now()
    t_now = t_start.strftime("%Y/%m/%d - %H:%M:%S")
    for i in range(5):
        try:
            socket.create_connection(("www.google.com",443))
            if verbose:
                print(f"\t[i] test connetion, time: {dt.now() - t_start} \tTRUE")
            if prev == False:
                logging.info(f"\t{t_now}\t[i] test connetion, time: {dt.now() - t_start} \tTRUE")
            return True
        except OSError:
            pass
    if verbose:
        print(f"\t[i] test connetion, time: {dt.now() - t_start} \tFALSE")
    if prev == True:
        logging.info(f"\t{t_now}\t[i] test connetion, time: {dt.now() - t_start} \tFALSE")
    return False



def check(chromium:bool, headless:bool, noimage:bool, nolocation:bool, mac:int, down:int, hard_c:int, verbose:bool, prev=None):
    while True:
        now = dt.now()
        if now-STARTED > timedelta(hours=4):
            restart(down=down, mac=mac, hard_c=hard_c)

        if is_connected(prev=prev):
            if down:
                lan_sharing(0)
                sleep(5)
                lan_sharing(1)

                t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
                if verbose:
                    print(f"\t{t_now}\tReconnected!\n")
                logging.info(f"\t{t_now}\tReconnected!\n")
            down = 0
            hard_c = 0
            prev = True

        else:
            if verbose:
                print("[i] down", down)
                print("[i] hard_c =", hard_c)
            if hard_c > 1:
                reboot(verbose=verbose)
                hard_c = 0
                pass

            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
            down += 1
            if down <= 1:
                lan_sharing(0)
            if verbose:
                print(f"\t{t_now}\tConnection Lost {down}...")
            logging.info(f"\t{t_now}\tConnection Lost {down}...")
            
            if down > 4:
                mac = renew_connection(mac=mac, verbose=verbose)
                hard_c += 1
                down = 1
            try:
                connect(chromium, headless, noimage, nolocation, verbose)
            except WebDriverException as err:
                err = '\\n'.join(str(err).split('\n')[0:2])
                t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
                if verbose:
                    print(f"\t{t_now}\t[!] ERRORE: check ")
                logging.error(f"\t{t_now}\t[!] ERRORE: check\t{err}")
                if down < 2:
                    soft_release(verbose)
                elif down == 2:
                    restart(down=down, mac=mac, hard_c=hard_c)
            prev = False

        sleep(10)



def connect(chromium: bool, headless: bool, noimage: bool, nolocation: bool, verbose: bool):
    driver = getDriver(chromium, headless, noimage, nolocation, verbose)
    
    link = "http://www.msftconnecttest.com/redirect"
    #link = "http://detectportal.firefox.com/canonical.html"
    
    driver.get(link)
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "email_field"))).send_keys(USR)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "password_field"))).send_keys(PWD)
        sleep(0.5)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "sign_in"))).click()
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")

        if verbose:
            print(f"\t{t_now}\tClick! 🖱")
        logging.info(f"\t{t_now}\tClick! 🖱")
    
        try:
            #TODO: simulare il caso in cui non sia accettata la connessione e vedere come è strutturata la pagina
            login_error = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, "login-error ")))
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
            if verbose:
                print(f"\t{t_now}\tlogin-error: Access Denied")
            logging.error(f"\t{t_now}\tlogin-error: Access Denied")
            renew_connection(mac=1, verbose=verbose)
            driver.close()
            connect(chromium, headless, noimage, nolocation, verbose)
        except TimeoutException:
            pass
        except NoSuchElementException:
            pass

    except Exception as err:
        driver.close()
        err = str(err).replace('\n',"\\n ")
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        if verbose:
            print(dt.now().strftime("%Y/%m/%d - %H:%M:%S")+f"\tconnect \t{err}")
        logging.error(f"\t{t_now}\tconnect \t{err}")

    for t in range(30):
        if is_connected(verbose=verbose): #or ("laziodisco.it" in driver.current_url)
            driver.close()
            return True
        sleep(1)
    driver.close()
    return False



def hard_release(min=30, verbose=False):
    if "linux" in platform.platform().lower():
        with subprocess.Popen(["sudo", "-S", "ip", "link", "set", wlan0, "down"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(60*min)

        subprocess.Popen(["sudo", "ip", "link", "set", wlan0, "up"])
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        sleep(60)


        if verbose:
            print(f"\t{t_now}\hard_release\t{min} Minutes of inactivity from wlan")
        logging.info(f"\t{t_now}\hard_release\t{min} Minutes of inactivity from wlan")
    
    
    else:
        pass
    
    for t in range(30):
        if is_connected(verbose=verbose):
            return
        sleep(1)



def soft_release(verbose=False):
    for t in range(10):
        if is_connected(verbose=verbose):
            return
        sleep(1)
    if "linux" in platform.platform().lower():
        #with subprocess.Popen(["sudo", "-S", "ip", "link", "set", wlan0, "down"], stdin=subprocess.PIPE) as proc:
        #    sleep(0.2)
        #    proc.communicate(f"{sudo_pwd}\n".encode())
        #sleep(5)
        #
        #subprocess.Popen(["sudo", "ip", "link", "set", wlan0, "up"])
        #sleep(10)

        with subprocess.Popen(["sudo", "-S", "dhclient", "-r", wlan0], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")

        if verbose:
            print(f"\t{t_now}\tsoft_release\tRelease the current IP addr from wireless interface")
        logging.info(f"\t{t_now}\tsoft_release\tRelease the current IP addr from wireless interface")
    
    else:
        pass

    for t in range(20):
        if is_connected(verbose=verbose):
            return
        sleep(1)



def renew_connection(mac: int, wait=True, log=True, verbose=False):
    t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
    if verbose:
        print(f"\t{t_now}\tRenewing connection")
    logging.info(f"\t{t_now}\tRenewing connection")
    #TODO: make for linux and for windows
    #TODO: deactivate wifi, change MAC address for wifi, clear dns
    if wait:
        for t in range(20):
            if is_connected(verbose=verbose):
                t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
                if verbose:
                    print(f"\t{t_now}\tRenew aborted")
                logging.info(f"\t{t_now}\tRenew aborted")
                return
            sleep(1)
    if "linux" in platform.platform().lower():
        mac = mac % len(MACs)
        MAC = MACs[mac]

        with subprocess.Popen(["ifconfig"], stdout=subprocess.PIPE) as proc:
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
            shell_out = proc.stdout.read()
            if MAC.lower() in str(shell_out).lower():
                mac = mac+1
                mac = mac % len(MACs)
                MAC = MACs[mac]

        with subprocess.Popen(["sudo", "-S", "ifconfig", wlan0, "down"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(1)
        subprocess.Popen(["sudo", "ip", "link", "set", wlan0, "down"])
        sleep(1)

        subprocess.Popen(["sudo", "ifconfig", wlan0, "hw", "ether", MAC])
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        sleep(1)
        subprocess.Popen(["sudo", "ip", "link", "set", wlan0, "up"])
        sleep(1)

        subprocess.Popen(["sudo", "ifconfig", wlan0, "up"])
        sleep(40)

        if verbose:
            print(f"\t{t_now}\tMAC address changed: {MAC}\tNEW!")
        logging.info(f"\t{t_now}\tMAC address changed: {MAC}\tNEW!")

        #with subprocess.Popen(["sudo", "-S", "dhclient", "-r", wlan0], stdin=subprocess.PIPE) as proc:
        #    sleep(0.2)
        #    proc.communicate(f"{sudo_pwd}\n".encode())
        #t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        #if verbose:
        #    print(f"\t{t_now}\tRelease the current IP addr from wireless interface")
        #logging.info(f"\t{t_now}\tRelease the current IP addr from wireless interface")
        sleep(10)
    
    else:
        t_now = dt.now().strftime("%Y/%m/%d - %H:%M:%S")
        task = subprocess.run(["ipconfig", "/release"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if log:
            logging.info(f"\t{t_now}\t{task}")
        sleep(3)

        t_now = dt.now().strftime("%Y/%m/%d - %H:%M:%S")
        task = subprocess.run(["ipconfig", "/flushdns"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if log:
            logging.info(f"\t{t_now}\t{task}")
        sleep(3)

        t_now = dt.now().strftime("%Y/%m/%d - %H:%M:%S")
        task = subprocess.run(["ipconfig", "/renew"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if log:
            logging.info(f"\t{t_now}\t{task}")
        else:
            logging.info(f"\t{t_now}\tRenewed!")

    mac = mac+1
    for t in range(30):
        if is_connected(verbose=verbose):
            return mac
        sleep(1)
    return mac



def main(chromium: bool, headless: bool, noimage: bool, nolocation: bool, mac:int, down:int, hard_c:int, verbose:bool):
    t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
    if verbose:
        print(f"\n{t_now}\tRestarted!")
    with open(f".{os.sep}connection.log", "a", encoding='UTF-8') as file:
        file.write('\n')
        file.flush()
    logging.info(f"\t{t_now}\tRestarted!")

    lan_sharing(0)
    sleep(5)
    while True:
        mac = (mac + 1) % len(MACs)
        try:
            if is_connected(verbose=verbose):
                lan_sharing(1)
            check(chromium, headless, noimage, nolocation, mac=mac, down=down, hard_c=hard_c, verbose=verbose)
        except KeyboardInterrupt:
            sys.exit("[i] Gracefully exit")

        except Exception as err:
            err = str(err).replace('\n',"\\n ")
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
            if verbose:
                print(f"\t{t_now}\t!!! ERRORE !!!")
            logging.error(f"\t{t_now}\t!!! ERRORE !!!\t{err}")

            lan_sharing(0)
            renew_connection(mac=mac, verbose=verbose)
            for t in range(30):
                if is_connected(verbose=verbose):
                    break
                sleep(1)




if __name__ == "__main__":
    if "linux" in platform.platform().lower():
        with subprocess.Popen(["sudo", "-S", "mkdir", "-p", "/usr/lib/chromedriver"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        subprocess.run(["sudo", "-S", "iwconfig", wlan0, "power", "off"])
        subprocess.run(["sudo", "-S", "chmod", "+x", f"/home/{WHOAMI}/lazio-disco_login/restart.sh"])

    try:
        try:
            opts, args = getopt.getopt(args=sys.argv[1:], shortopts=shortopts, longopts=longopts)
        except getopt.GetoptError as e:
            print(f"{e}")
            sys.exit("[i] Gracefully exit")

        chromium = False
        headless = False
        noimage = False
        nolocation = False
        verbose = False
        doexit = False
        mac = 1
        down = 0
        hard_c = 0

        for opt, arg in opts:
            if opt in ["-h", "--help"]:
                help()
                doexit = True
            elif opt in ["-c", "--chromium"]:
                chromium = True
            elif opt in ["-H", "--headless"]:
                headless = True
            elif opt in ["-i", "--noimage"]:
                noimage = True
            elif opt in ["-l", "--nolocation"]:
                nolocation = True
            elif opt in ["-C", "--hard_c"]:
                try:
                    hard_c = int(arg.strip())
                except ValueError:
                    pass
            elif opt in ["-d", "--down"]:
                try:
                    down = int(arg.strip())
                except ValueError:
                    pass
            elif opt in ["-m", "--mac_address"]:
                try:
                    mac_address = int(arg.strip())
                except ValueError:
                    pass
            elif opt in ["-v", "--verbose"]:
                verbose = True
            elif opt in ["-V", "--version"]:
                version()
                doexit = True

        if not doexit:
            main(chromium=chromium, headless=headless, noimage=noimage, nolocation=nolocation, mac=mac, down=down, hard_c=hard_c, verbose=verbose)
    except KeyboardInterrupt:
        sys.exit("[i] Gracefully exit")
