#!/usr/bin/python
import wb5m2
import os


#codehome = "/home/eddie7/code/"
codehome = "/Users/martin/Baseball/WhiskeyBall/Code"

# calculate and write stats
wb5m2.DoTheDay()

# Now cp stuff to my web page
os.system('/usr/local/bin/sshpass -p notTheRealPasswd scp -o User=dandre -o StrictHostKeyChecking=no ' + codehome + '/wb5m2/* shinteki.com:public_html/davidandre/wb/')
