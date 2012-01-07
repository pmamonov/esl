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
    self.lim={'t':(1,0xffff, 'T, ms', ms2tick),
              'n':(1,0xffff, 'N', 1),
              't1':(1,0xffff, 'T1, ms',ms2tick),
              'w':(1,0xffff, 'w, ms',ms2tick),
              'a':(0,1023,'A, mV',1)}
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

    if p['n']*p['t1']>p['t'] or p['w']>p['t1']: raise NameError, "Inconsistent parameters values"
    self.cmd(2,struct.pack("<hhhhh", *map(lambda k: self.lim[k][3]*p[k], ('t','n','t1','w','a'))))
    return p

if __name__=="__main__":
  from Tkinter import *
  from tkMessageBox import showerror

  def apply_params():
    global esl,p_inputs
    p_vals={}
    try:
      for k in p_inputs.keys(): p_vals[k]=float(p_inputs[k].get())
      p_vals=esl.set_params(**p_vals)
    except:
      showerror("ERROR", sys.exc_info()[1])
    else:
      for k in p_inputs.keys():
        p_inputs[k].delete(0,END)
        p_inputs[k].insert(0,str(p_vals[k]))
  
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

  for k in esl.lim.keys():
    mn,mx,label,confac = esl.lim[k]
    Label(frLabels,text=label).pack(side=TOP,anchor='nw')
    en=Entry(frInputs)
    en.pack(side=TOP,anchor='nw')
    p_inputs[k]=en
    Label(frLims,text= "%.2f - %.2f"%tuple(map(lambda v: v/confac, (mn,mx))) ).pack(side=TOP,anchor='nw')
  """
  Label(frLabels,text="N").pack(side=TOP,anchor='nw')
  enN=Entry(frInputs)
  enN.pack(side=TOP,anchor='nw')
  p_inputs['n']=enN

  Label(frLabels,text="T1, ms").pack(side=TOP,anchor='nw')
  enT1=Entry(frInputs)
  enT1.pack(side=TOP,anchor='nw')
  p_inputs['t1']=enT1

  Label(frLabels,text="w, ms").pack(side=TOP,anchor='nw')
  enW=Entry(frInputs)
  enW.pack(side=TOP,anchor='nw')
  p_inputs['w']=enW

  Label(frLabels,text="A, mV").pack(side=TOP,anchor='nw')
  enA=Entry(frInputs)
  enA.pack(side=TOP,anchor='nw')
  p_inputs['a']=enA
  """

  Button(frBut, text="Apply",command=apply_params).pack(side=LEFT)
  Button(frBut, text="Start", command=esl.start).pack(side=LEFT)
  Button(frBut, text="Single", command=lambda: showerror("Not Implemented", "This function is not implemented yet")).pack(side=LEFT)
  Button(frBut, text="Stop",command=esl.stop).pack(side=LEFT)
  root.mainloop()
