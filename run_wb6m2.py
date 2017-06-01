#!/usr/bin/python
import wb6m2
import os


codehome = "/home/eddie7/code/"
#codehome = "/Users/martin/Baseball/WhiskeyBall/Code"

# calculate and write stats
wb6m2.DoTheDay()

# Now cp stuff to my web page
os.system('/usr/bin/sshpass -p dr4g0nBuff4l0D1n0Truck! scp -o User=dandre -o StrictHostKeyChecking=no ' + codehome + '/wb6m2/* shinteki.com:public_html/davidandre/wb/')




