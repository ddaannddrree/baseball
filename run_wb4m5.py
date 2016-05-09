import wb4m5
import os

wb4m5.DoTheDay()
#Now cp stuff to my web page

os.system('sshpass -p f4m1n3G4m3 scp -o User=dandre -o StrictHostKeyChecking=no /home/eddie7/code/wb4m5/* shinteki.com:public_html/davidandre/wb/')
