import usb, struct
ms2tick = 12e3/256

class usbstub:
  def __init__(self):
    pass

  def controlMsg(self, reqtype, req, l):
    print "(%d)"%req
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

  def single(self):
    self.cmd(3)

  def stop(self):
    self.cmd(0)

  def set_params(self,**p):
    if p['n']*p['t1']>p['t'] or p['w']>p['t1']: raise NameError, "Inconsistent parameters values"
    s=struct.pack("<HHHHH", *map(lambda k: p[k], ('t','n','t1','w','a')))
    for c in s: print "%02x "%ord(c),
    print ""
    self.cmd(2,struct.pack("<HHHHH", *map(lambda k: p[k], ('t','n','t1','w','a'))))



if __name__=="__main__":
  from Tkinter import *
  from tkMessageBox import showerror,showinfo
  import tkFont, tkFileDialog
  from time import time,sleep
  import os.path

  def parvalidate (event):
    global p_inputs,p_limits
    k=event.widget.esl_input_name
    ptxt=p_inputs[k].get()
    if len(ptxt):
      mn,mx,c,typ = map(lambda k1: p_limits[k][k1], ('min','max','c','typ'))
      pval=typ(ptxt)
      if pval < mn/c: pval=mn/c
      if pval > mx/c: pval=mx/c
      ptxt=str(pval)
      p_inputs[k].set(ptxt)

      ms2hz={'t':'1/t','1/t':'t','t1':'1/t1','1/t1':'t1'}
      if k in ms2hz.keys():
        p_inputs[ms2hz[k]].set(str(1e3/pval))

      if len(p_inputs['n'].get()):
        if int(p_inputs['n'].get())==1 and k in ('t','1/t','n','w'):
          if len(p_inputs['t'].get()):
            p_inputs['t1'].set(p_inputs['t'].get())
            p_inputs['1/t1'].set(p_inputs['1/t'].get())
          elif len(p_inputs['w'].get()):
            p_inputs['t1'].set(p_inputs['w'].get())
            p_inputs['1/t1'].set(1e3/float(p_inputs['w'].get()))

    return False

  def load(f):
    if os.path.isfile(f):
      fd=open(f)
      for s in fd:
        k,v=s.split()
        p_inputs[k].set(v)
      fd.close()

  def save(f):
    print f
    fd=open(f,'w')
    for k in p_inputs.keys():
      v=p_inputs[k].get()
      if not len(v): v="0"
      print >>fd, "%s %s"%(k,v)
    fd.close()

  def apply_params():
    global esl,p_inputs,p_limits
    p_vals={}
    try:
      for k in p_inputs.keys(): p_vals[k]=p_limits[k]['c']*float(p_inputs[k].get())
      esl.set_params(**p_vals)
    except:
      showerror("ERROR", sys.exc_info()[1])
      raise NameError, "Failed to update stimulation parameters."

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
    esl.stop()
    try:
      apply_params()
    except NameError, err:
      showerror("ERROR", err)
    else:
      esl.single()

    """
    T=0xffff/ms2tick
    t=p_inputs['t'].get()
    t1=float(p_inputs['t1'].get())
    n=float(p_inputs['n'].get())

    if (n*t1+100) > T: 
      s="Pulse train is too long. Adjust parameters so that (N*T1 + 100) < Tmax."
      showerror("ERROR", s)
      raise NameError, s

    p_inputs['t'].delete(0,END); p_inputs['t'].insert(0,str(T))
    esl.stop()
    start()
    sleep(1e-3*(n*t1+50))
    esl.stop()
    p_inputs['t'].delete(0,END); p_inputs['t'].insert(0,t)
    """


  p_limits={'t':{'min':1,'max':0xffff,'label':'T, ms','c':ms2tick,'typ':float},
           'n':{'min':1,'max':0xffff,'label':'N', 'c':1,'typ':int},
           't1':{'min':1,'max':0xffff,'label':'T1, ms','c':ms2tick,'typ':float},
           'w':{'min':1,'max':0xffff,'label':'w, ms','c':ms2tick,'typ':float},
           'a':{'min':1,'max':1023,'label':'A, mV','c':1./8,'typ':float},
           '1/t':{'max':1./1,'min':1./0xffff,'label':'1/T, Hz','c':1e-3/ms2tick,'typ':float},
           '1/t1':{'max':1./1,'min':1./0xffff,'label':'1/T1, Hz','c':1e-3/ms2tick,'typ':float}
           }

  p_inputs={}

  try:
  	esl=ESL(usestub=True)
#    esl=ESL(usestub=False)
  except NameError:
  	showerror("ERROR", "Device not found. Fire up your soldering iron, hacker!")
  	sys.exit(1)
  	

  root=Tk()
  root.title("ElectroStimuLator")
  root.resizable(0,0)
  fnt=tkFont.Font(font=("Helvetica",14,NORMAL))
  root.option_add("*Font", fnt)

  pic=PhotoImage(file="imp.gif", master=root)
  lpic=Label(root,image=pic )
  lpic.pack(side=TOP)

  frMnu=Frame(root)
  frMnu.pack(side=TOP)
  Button(frMnu, text="Load", command=lambda: load(tkFileDialog.askopenfilename())).pack(side=LEFT)
  Button(frMnu, text="Save", command=lambda: save(tkFileDialog.asksaveasfilename())).pack(side=LEFT)
  Button(frMnu, text="Quit", command=root.destroy).pack(side=LEFT)

  frInp=Frame(root)
  frInp.pack(side=TOP)

  frLabels=Frame(frInp)
  frLabels.pack(side=LEFT)
  frInputs=Frame(frInp)
  frInputs.pack(side=LEFT)
  frLims=Frame(frInp)
  frLims.pack(side=LEFT)

  for k in ('t','1/t','n','t1','1/t1','w','a'):
    mn,mx,label,confac,typ = map(lambda k1: p_limits[k][k1], ('min','max','label','c','typ'))
    Label(frLabels,text=label).pack(side=TOP,anchor='nw')
    vtxt=StringVar()
    en=Entry(frInputs, width=7, textvariable=vtxt)
    en.pack(side=TOP,anchor='nw')
    en.bind("<FocusOut>", parvalidate)
    en.esl_input_name=k
    p_inputs[k]=vtxt
#    Label(frLims,text= "%.2f - %.2f"%tuple(map(lambda v: v/confac, (mn,mx))) ).pack(side=TOP,anchor='nw')
    Label(frLims,text=str(typ(round(mn/confac,2)))+" - "+str(typ(round(mx/confac,2))) ).pack(side=TOP,anchor='nw')


  frBut=Frame(root)
  frBut.pack(side=TOP)
#  Button(frBut, text="Apply",command=apply_params).pack(side=LEFT)
  Button(frBut, text="Start", command=start).pack(side=LEFT)
  Button(frBut, text="Single", command=single).pack(side=LEFT)
  Button(frBut, text="Stop",command=esl.stop).pack(side=LEFT)
  showinfo("HINT", "HINT: Use TAB / SHIFT+TAB to jump between controls. Use SPACE to push buttons.")
  root.mainloop()
