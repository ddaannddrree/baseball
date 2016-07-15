#!/usr/bin/python
import wb5m3
import os


codehome = "/home/eddie7/code/"
#codehome = "/Users/martin/Baseball/WhiskeyBall/Code"

# calculate and write stats
wb5m3.DoTheDay()

# Now cp stuff to my web page
os.system('/usr/bin/sshpass -p wh4tTh3B4n4n4! scp -o User=dandre -o StrictHostKeyChecking=no ' + codehome + '/wb5m3/* shinteki.com:public_html/davidandre/wb/')
