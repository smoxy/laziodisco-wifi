#! /usr/bin/bash

cd /home/$(whoami)/lazio-disco_login/

if [ -z "$3" ]; then
    sleep 10
    /home/$(whoami)/py_venv/laziodisco/bin/python /home/$(whoami)/lazio-disco_login/main.py -l -H -v -c

    #screen -S wifi.login -dm /home/$(whoami)/py_venv/laziodisco/bin/python /home/$(whoami)/lazio-disco_login/main.py -l -H -v -c
else
    sleep 5
    screen -S wifi.login -dm /home/$(whoami)/py_venv/laziodisco/bin/python /home/$(whoami)/lazio-disco_login/main.py -l -H -v -c --down $1 --mac_address $2 --hard_c $3

fi

#cd /home/$(whoami)/lazio-disco_login/
#screen -S wifi.login -dm /home/$(whoami)/py_venv/laziodisco/bin/python /home/$(whoami)/lazio-disco_login/main.py -l -H -v -c --down $1 --mac_address $2 --hard_c $3
#sleep 40

#sleep 10 && \
#  cd /home/$(whoami)/lazio-disco_login/ && \
#  /home/$(whoami)/py_venv/laziodisco/bin/python /home/$(whoami)/lazio-disco_login/main.py -l -H -v -c --down $1 --mac_address $2 --hard_c $3
