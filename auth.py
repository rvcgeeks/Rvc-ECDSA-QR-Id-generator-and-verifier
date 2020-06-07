#
# An elliptic curve digital signature algorithm QR code id generator
# and verifier using camera with arduino firmata support 
# in pure python compatable for beaglebone and raspberry pi.
# ideal for databaseless client authorisation using camera on Rpi
#
# created by rvcgeeks <github.com/rvcgeeks> (rvchavadekar@gmail.com) @ Pune, India on 7 June 2020.
#

from sys import argv
from ecdsa import *

H = 0xdeadbeef  # just a default hash value ;)

if argv[1] == 's':

  from qrcode import make 

  try:
    f = open('keys/' + argv[2], 'r')
  except:  # generate key file if not found
    prvk, pubk = keygen()
    f = open('keys/' + argv[2], 'w')
    f.write('%s\n%s,%s' % (itob58(prvk), itob58(pubk[0]), itob58(pubk[1])))
    f.close();
    f = open('keys/' + argv[2], 'r')
  
  l = f.readlines()
  f.close()
  prvk = b58toi(l[0][:-1]) # cuz of \n
  i, n = 0, 1 if len(argv) == 3 else int(argv[3])
  
  while i < n:
    sig = sign(prvk, H)
    img = make('%s,%s' % (itob58(sig[0]), itob58(sig[1]))) #generate QRcode   
    img.save('credentials/cred_'+ argv[2] + '_' + str(i) + '.png')
    i += 1

elif argv[1] == 'v':
  
  import cv2
  from pyzbar import pyzbar
  
  board = None
  try: # No worries if you don't have arduino.. its for attaching motor for door lock or barrier boom system.. atleast you have the terminal or command prompt 
    
    from pyfirmata import Arduino
    from os import name
    
    if name == 'nt': # check if windows OS ... device driver structure for usb is different in linux
      board = Arduino('COM3')
    else: # in linux name is 'posix' .. works for Raspberry Pi
      board = Arduino('/dev/ttyACM0') # goto arduino ide -> examples -> Firmata -> StandardFirmata and burn it into board before
      
    board.digital[12].write(0)
    board.digital[13].write(0)
  
  except:
    pass
  
  f = open('keys/' + argv[2], 'r')
  kl = f.readlines()
  f.close()
  pks = kl[1].split(',')
  pubk = (b58toi(pks[0]), b58toi(pks[1]))
  
  status = 0; prevstatus = 0; i = 0; maxframesmsg = 50
  cap = cv2.VideoCapture(0)

  while True:
    
    _, frame = cap.read()
    data = pyzbar.decode(frame) 
    
    if data and status == 0:      
      try:  # by chance if code is successfully decoded but with malformed data .. signature parsing may create exceptions
        sg = data[0].data.decode().split(',') # only 1 qr present in video
        sig = (b58toi(sg[0]), b58toi(sg[1]))
        status = 1 if verify(pubk, H, sig) else -1
      except:
        pass
    
    if status != 0:
      if i < maxframesmsg:
        i += 1
      else:
        status = 0
        i = 0
    
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1)
    if key == ord('x'): # press 'x' key on keyboard to exit
      break
    
    if status != prevstatus:
      print('\033[2J\033[1;1H')
      if status == 1:
        print('VERIFIED OK')
        if board:
          
          # DO ARDUINO ACTIONS IF VERIFIED HERE ... because I dont know what actuators you want to trigger after authorisation
          board.digital[12].write(0)   # program them here accordingly
          board.digital[13].write(1)
        
      elif status == -1:
        print('NOT AUTHORISED')
        if board:
          
          # DO ARDUINO ACTIONS IF NOT VERIFIED HERE
          board.digital[12].write(1)
          board.digital[13].write(0)
        
      else:
        if board:
          
          # DO ARDUINO ACTIONS IF IDLE HERE
          board.digital[12].write(0)
          board.digital[13].write(0)
    
    prevstatus = status
    
  cap.release()
  cv2.destroyAllWindows()
