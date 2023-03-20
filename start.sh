#! /usr/bin/bash

sleep 10 && \
  cd /home/smoxy/lazio-disco_login/ && \
  /home/smoxy/py_venv/laziodisco/bin/python /home/smoxy/lazio-disco_login/main.py -l -H -v -c

## crontab -e
#@reboot screen -S wifi.login -dm /home/smoxy/lazio-disco_login/start.sh
