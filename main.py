import platform
import os
import socket
import logging
import sys
import getopt
import subprocess

from time import sleep
from datetime import datetime as dt

from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

from config import *



logging.basicConfig(filename=f".{os.sep}connection.log", encoding="utf-8", level=logging.INFO)

V="0.2"
shortopts = '''hcHilvV''' #if after the letter there is ':' the argument is required
longopts = ["help", "chromium", "headless", "noimage", "nolocation", "verbose", "version"] #if after name variable there is '=' the argument is required



def help():
    print(f"""LazioDisco wifi {V}
(C) 2022-2023 Simone Flavio Paris.
Released under Apache License 2.0
    -h --help               Print this help screen.
    -c --chromium           Use chromium browser instead of Chrome.
    -H --headless           Use this script in headless mode.
    -i --noimage            Reduce bandwidth waste disabling image loading.
    -l --nolocation         Don't allow sites to track your physical location.
    -v --verbose            Print to screen all messages.
    -V --version            Print version info.
    """)

def version():
    print(f"auto DiscoLogin {V}")



def lan_sharing(power: bool):
    return
    if power:
        try:
            with subprocess.Popen(["sudo", "-S", "wg-quick", "up", "wg1"], stdin=subprocess.PIPE) as proc:
                sleep(0.2)
                proc.communicate(f"{sudo_pwd}\n".encode())
            sleep(1)
        except:
            pass
        with subprocess.Popen(["sudo", "-S", "ip", "link", "set", eth0, "up"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(1)
        with subprocess.Popen(["sudo", "-S", "ifconfig", eth0, "up"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(1)
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        logging.info(f"\t{t_now}\tWireguard and {eth0} turned ON!\n")
    else:
        with subprocess.Popen(["sudo", "-S", "ifconfig", eth0, "down"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(1)
        subprocess.Popen(["sudo", "ip", "link", "set", eth0, "down"])
        sleep(1)
        try:
            subprocess.Popen(["sudo", "wg-quick", "down", "wg1"])
            sleep(1)
        except:
            pass
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        logging.info(f"\t{t_now}\t{eth0} and Wireguard turned OFF!\n")



def getDriver(chromium: bool, headless: bool, noimage: bool, nolocation: bool, verbose: bool):
    locale = "en"
    chrome_options = Options()
    chrome_options.add_argument(f"--lang={locale}")
    chrome_options.add_argument("start-maximized")
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

    if not ("raspi" in platform.platform().lower() or "aarch" in platform.platform().lower()): #or "linux" in platform.platform().lower()
        if chromium:
            path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        else:
            try:
                path = ChromeDriverManager().install()
            except:
                path = b"/home/smoxy/.wdm/drivers/chromedriver/linux64/109.0.5414/chromedriver"
        if verbose:
            print("browser driver path:",path)

        driver = webdriver.Chrome(service=Service(path), options=chrome_options)
    else: #If under arm, raspi or aarch
        # you have to download the right driver and put here the path
        if chromium:
            driver = webdriver.Chrome(service=Service(f"{os.sep}usr{os.sep}lib{os.sep}chromium-browser{os.sep}chromedriver"), options=chrome_options)
    
    return driver



def is_connected():
    try:
        socket.create_connection(("8.8.8.8",53),timeout=2)
        return True
    except OSError:
        pass
    return False



def check(chromium: bool, headless: bool, noimage: bool, nolocation: bool, verbose: bool, mac: int):
    down = int(not is_connected())

    while True:
        if is_connected():
            if down:
                lan_sharing(True)

                t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
                if verbose:
                    print(f"{t_now}\tReconnected!")
                logging.info(f"\t{t_now}\tReconnected!\n")
            down = 0
        else:
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
            down += 1
            if down > 1:
                lan_sharing(False)
            if verbose:
                print(f"{t_now}\tConnection Lost {down}...")
            logging.info(f"\t{t_now}\tConnection Lost {down}...")
            
            if down > 4:
                mac = renew_connection(log=True, verbose=verbose, mac=mac)
                down = 1
            elif down > 2:
                connectV2(chromium, headless, noimage, nolocation, verbose=verbose)
        sleep(10)
                


def connectV2(chromium: bool, headless: bool, noimage: bool, nolocation: bool, verbose: bool):
    driver = getDriver(chromium, headless, noimage, nolocation, verbose)
    
    #link = "http://www.msftconnecttest.com/redirect"
    link = "http://detectportal.firefox.com/canonical.html"

    if "linux" in platform.platform().lower():
        with subprocess.Popen(["sudo", "-S", "ip", "link", "set", wlan0, "down"], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        sleep(5)

        subprocess.Popen(["sudo", "ip", "link", "set", wlan0, "up"])
        sleep(5)

        subprocess.Popen(["sudo", "dhclient", "-r", wlan0])
        sleep(3)
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        if verbose:
            print(f"{t_now}\tRelease the current IP addr from wireless interface")
        logging.info(f"\t{t_now}\tRelease the current IP addr from wireless interface")
    
    else:
        pass

    driver.get(link)
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "email_field"))).send_keys(USR)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "password_field"))).send_keys(PWD)
        sleep(0.5)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "sign_in"))).click()
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")

        if verbose:
            print(f"{t_now}\tClick! 🖱")
        logging.info(f"\t{t_now}\tClick! 🖱")
    
        try:
            login_error = WebDriverWait(driver, 15, ignored_exceptions=(NoSuchElementException, StaleElementReferenceException,))\
                        .until(EC.presence_of_element_located((By.CLASS_NAME, "login-error ")))
            #login_error  = driver.find_element(By.CLASS_NAME, "login-error ")
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
            if verbose:
                print(f"\t{t_now}\tlogin-error: {login_error}\n{type(login_error)}")
            logging.error(f"\t{t_now}\tlogin-error: {login_error}\n{type(login_error)}")

            #renew_connection(log=True, verbose=verbose, mac=1)

        except TimeoutException:
            pass
        except NoSuchElementException:
            pass

    except Exception as err:
        err = str(err).replace('\n',"; ")
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        if verbose:
            print(dt.now().strftime("%Y/%m/%d - %H:%M:%S")+f"\t{err}")
        logging.error(f"\t{t_now}\t{err}")
        driver.close()
    for t in range(30):
        if is_connected():
            return True
        sleep(1)
    return False



def renew_connection(mac: int, wait=True, log=False, verbose=False):
    #TODO: make for linux and for windows
    #TODO: deactivate wifi, change MAC address for wifi, clear dns
    if wait:
        for t in range(30):
            sleep(1)
            if is_connected():
                t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
                if verbose:
                    print(f"\t{t_now}\tRenew aborted")
                logging.info(f"\t{t_now}\tRenew aborted")
                return
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
        sleep(3)

        subprocess.Popen(["sudo", "ifconfig", wlan0, "hw", "ether", MAC])
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        if verbose:
            print(f"\t{t_now}\tMAC address changed: {MAC}\tNEW!")        
        logging.info(f"\t{t_now}\tMAC address changed: {MAC}\tNEW!")        
        sleep(5)

        subprocess.Popen(["sudo", "ifconfig", wlan0, "up"])
        sleep(5)

        with subprocess.Popen(["sudo", "dhclient", "-r", wlan0], stdin=subprocess.PIPE) as proc:
            sleep(0.2)
            proc.communicate(f"{sudo_pwd}\n".encode())
        t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
        if verbose:
            print(f"{t_now}\tRelease the current IP addr from wireless interface")
        logging.info(f"\t{t_now}\tRelease the current IP addr from wireless interface")
    
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
    return mac



def main(chromium: bool, headless: bool, noimage: bool, nolocation: bool, verbose:bool):
    t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
    if verbose:
        print(f"{t_now}\tRestarted!")
    logging.info(f"\t{t_now}\tRestarted!")
    mac = 0
    while True:
        mac = (mac + 1) % len(MACs)
        try:
            check(chromium, headless, noimage, nolocation, verbose=verbose, mac=mac)
        except KeyboardInterrupt:
            sys.exit()
            quit()
        except Exception as err:
            err = str(err).replace('\n',"; ")
            t_now = (dt.now()).strftime("%Y/%m/%d - %H:%M:%S")
            if verbose:
                print(f"{t_now}\t!!! ERRORE !!!")
            logging.error(f"\t{t_now}\t!!! ERRORE !!!\t{err}")
            lan_sharing(0)
            renew_connection(log=True, wait=True, verbose=verbose, mac=mac)
            lan_sharing(1)



if __name__ == "__main__":
    try:
        try:
            opts, args = getopt.getopt(args=sys.argv[1:], shortopts=shortopts, longopts=longopts)
        except getopt.GetoptError as e:
            print(f"{e}")
            print("[i] Gracefully exit")
            quit()

        chromium = False
        headless = False
        noimage = False
        nolocation = False
        verbose = False
        doexit = False

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
            elif opt in ["-v", "--verbose"]:
                verbose = True
            elif opt in ["-V", "--version"]:
                version()
                doexit = True

        if not doexit:
            main(chromium=chromium, headless=headless, noimage=noimage, nolocation=nolocation, verbose=verbose)
    except KeyboardInterrupt:
        print("[i] Gracefully exit")
        quit()
