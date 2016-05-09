import wb5m1
import os

wb5m1.DoTheDay()
#Now cp stuff to my web page

os.system('sshpass -p f4m1n3G4m3 scp -o User=dandre -o StrictHostKeyChecking=no /home/eddie7/code/wb5m1/* shinteki.com:public_html/davidandre/wb/')
