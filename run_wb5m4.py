#!/usr/bin/python
import wb5m4
import os


codehome = "/home/eddie7/code/"
#codehome = "/Users/martin/Baseball/WhiskeyBall/Code"

# calculate and write stats
wb5m4.DoTheDay()

# Now cp stuff to my web page
os.system('/usr/bin/sshpass -p dr4g0nBuff4l0D1n0Truck! scp -o User=dandre -o StrictHostKeyChecking=no ' + codehome + '/wb5m4/* shinteki.com:public_html/davidandre/wb/')




