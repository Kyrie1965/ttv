opkg update
opkg install wget ca-certificates python3 nginx cron

wget --no-check-certificate -O /opt/bin/ttv.py https://raw.githubusercontent.com/Kyrie1965/ttv/master/ttv.py

python3 /opt/bin/ttv.py
