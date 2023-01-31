# laziodisco-wifi
This is a little script with the aim of automate login process into laziodisco caption portal.
Works with chrome and chromium.

If you want the best results plan to execute this script after the reboot.


## requirements

 > pip install selenium==4.8.0
 >
 > pip install webdriver-manager==3.8.5

## first steps
Edit config.py by:
 - changing username and password with the provided one by laziodisco.
 - filling the list with MAC addresses. The first element is the real MAC address, all others must be generated.
   - You could generate a mac address whit this command under linux:
   - > tr -dc A-F0-9 < /dev/urandom | head -c 10 | sed -r 's/(..)/\1:/g;s/:$//;s/^/02:/'
 - changing the interface names
 
## help
 >     -h --help               Print this help screen and exit.
 >
 >     -c --chromium           Use chromium browser instead of Chrome.
 >
 >     -H --headless           Use this script in headless mode.
 >
 >     -i --noimage            Reduce bandwidth waste disabling image loading.
 >
 >     -l --nolocation         Don't allow sites to track your physical location.
 >
 >     -v --verbose            Print to screen all messages.
 >
 >     -V --version            Print version info and exit.
