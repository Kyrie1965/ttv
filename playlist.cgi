#!/bin/sh
PATH=/opt/sbin:/opt/bin:/opt/usr/sbin:/opt/usr/bin:/usr/sbin:/usr/bin:/sbin:/bin

python3 /opt/etc/ttv/ttv.py
echo "Content-Type: text/plain; charset=UTF-8"
echo ""
echo "$(cat /opt/etc/ttv//playlist.m3u)"