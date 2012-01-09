import usb, struct
ms2tick = 12e3/256

class usbstub:
  def __init__(self):
    pass

  def controlMsg(self, reqtype, req, l):
    if type(l) is int:
      return tuple(range(l))
    else:
      for s in l: print "%02X"%ord(s),
      print ""
      return 0

class ESL:
  idVendor = 0x16c0
  idProduct = 0x05dc
  Manufacturer = "piton"
  Product = "ESL"

  def __init__(self, usestub=False):
    self.lim={'1t':(1,0xffff, 'T, ms', ms2tick),
              '2n':(1,0xffff, 'N', 1),
              '3t1':(1,0xffff, 'T1, ms',ms2tick),
              '4w':(1,0xffff, 'w, ms',ms2tick),
              '5a':(0,1023,'A, ?',1)}
    self.usestub=usestub
    self.reconnect()

  def reconnect(self):
    self.devh=None
    for bus in usb.busses():
      for dev in bus.devices:
        if dev.idVendor == self.idVendor and dev.idProduct == self.idProduct:
          devh = dev.open()
          if devh.getString(dev.iManufacturer, len(self.Manufacturer)) == self.Manufacturer and  devh.getString(dev.iProduct, len(self.Product)) == self.Product:
            self.devh = devh
            print "Device found."
    if not self.devh:
      if self.usestub:
        print >>sys.stderr, "WARNING: Device NOT found! Using software stub."
        self.devh=usbstub()
      else:
        raise NameError, "Device not found"
  
  def cmd(self, cmd, buf=None):
    ok=False
#    retry_count=1
#    while not ok and retry_count:
    while not ok:
      try:
        if buf:
          self.devh.controlMsg(usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_OUT, cmd,buf)
        else:
          self.devh.controlMsg(usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_IN, cmd,0)
        ok=True
      except usb.USBError as usberr:
        print "USBError:", usberr
        self.reconnect()
#        retry_count-=1
      except AttributeError:
        self.reconnect()

  def start(self):
    self.cmd(1)

  def stop(self):
    self.cmd(0)

  def set_params(self,**p):
    for k,v in p.items():
      mn,mx,label,confac=self.lim[k]
      if v*confac < mn: p[k]=mn/confac
      if v*confac > mx: p[k]=mx/confac

    if p['2n']*p['3t1']>p['1t'] or p['4w']>p['3t1']: raise NameError, "Inconsistent parameters values"
    self.cmd(2,struct.pack("<HHHHH", *map(lambda k: self.lim[k][3]*p[k], ('1t','2n','3t1','4w','5a'))))
    return p

if __name__=="__main__":
  from Tkinter import *
  from tkMessageBox import showerror
  from time import time,sleep

  def apply_params():
    global esl,p_inputs
    p_vals={}
    try:
      for k in p_inputs.keys(): p_vals[k]=float(p_inputs[k].get())
      p_vals=esl.set_params(**p_vals)
    except:
      showerror("ERROR", sys.exc_info()[1])
      raise NameError, "Failed to update stimulation parameters."
    else:
      for k in p_inputs.keys():
        p_inputs[k].delete(0,END)
        p_inputs[k].insert(0,str(p_vals[k]))

  def start():
    global esl
    try:
      apply_params()
    except NameError, err:
      showerror("ERROR", err)
    else:
      esl.start()

  def single():
    global esl,p_inputs
    T=0xffff/ms2tick
    t=p_inputs['1t'].get()
    t1=float(p_inputs['3t1'].get())
    n=float(p_inputs['2n'].get())

    if (n*t1+100) > T: 
      s="Pulse train is too long. Adjust parameters so that (N*T1 + 100) < Tmax."
      showerror("ERROR", s)
      raise NameError, s

    p_inputs['1t'].delete(0,END); p_inputs['1t'].insert(0,str(T))
    esl.stop()
    start()
    sleep(1e-3*(n*t1+50))
    esl.stop()
    p_inputs['1t'].delete(0,END); p_inputs['1t'].insert(0,t)

  p_inputs={}

  try:
#  	esl=ESL(usestub=True)
    esl=ESL(usestub=False)
  except NameError:
  	showerror("ERROR", "Device not found. Ask KUZYA for one.")
  	sys.exit(1)
  	

  root=Tk()
  root.title("ElectroStimuLator")
  root.resizable(0,0)
  
  pic=PhotoImage(file="imp.gif", master=root)
  lpic=Label(root,image=pic )
  lpic.pack(side=TOP)

  frInp=Frame(root)
  frInp.pack(side=TOP)
  frBut=Frame(root)
  frBut.pack(side=TOP)

  frLabels=Frame(frInp)
  frLabels.pack(side=LEFT)
  frInputs=Frame(frInp)
  frInputs.pack(side=LEFT)
  frLims=Frame(frInp)
  frLims.pack(side=LEFT)

  for k in sorted(esl.lim.keys()):
    mn,mx,label,confac = esl.lim[k]
    Label(frLabels,text=label).pack(side=TOP,anchor='nw')
    en=Entry(frInputs)
    en.pack(side=TOP,anchor='nw')
    p_inputs[k]=en
    Label(frLims,text= "%.2f - %.2f"%tuple(map(lambda v: v/confac, (mn,mx))) ).pack(side=TOP,anchor='nw')

  Button(frBut, text="Apply",command=apply_params).pack(side=LEFT)
  Button(frBut, text="Start", command=start).pack(side=LEFT)
  Button(frBut, text="Single", command=single).pack(side=LEFT)
  Button(frBut, text="Stop",command=esl.stop).pack(side=LEFT)
  root.mainloop()
