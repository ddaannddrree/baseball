import wb4m3
import os

wb4m3.DoTheDay()
#Now cp stuff to my web page

os.system('sshpass -p f4m1n3G4m3 scp -o User=dandre -o StrictHostKeyChecking=no /home/eddie7/code/wb4m3/* shinteki.com:public_html/davidandre/wb/')
