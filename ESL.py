import usb, struct, sys
ms2tick = 12e3/256

CMD_STOP =      0
CMD_START =     1
CMD_PARAMS =    2
CMD_SINGLE =    3
CMD_GETPARAMS = 4
CMD_STORE =     5
CMD_LOAD =      6
CMD_TRIG_EN =   7
CMD_TRIG_DIS =  8

V0 = 0
V1 = 1

PSZ_V0 = 10
PSZ_V1 = 14

PSZ = {
  V0 : PSZ_V0,
  V1 : PSZ_V1,
}

FMT = {
  V0 : "<HHHHH",
  V1 : "<xxLHHHH",
}

def list2str(l):
  return reduce(lambda s, n: s + chr(n), l, "")

class usbstub:
  def __init__(self):
    pass

  def controlMsg(self, reqtype, req, l, timeout):
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
  psz = 0
  ver = 0

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
        print "WARNING: Device NOT found! Using software stub."
        self.devh=usbstub()
      else:
        raise NameError, "Device not found. Fire up your soldering iron, hacker!"
    else:
      # detect firmware version
      r = self.cmd(CMD_GETPARAMS, 100)
      self.psz = len(r)
      if self.psz == PSZ[V0]:
        self.ver = V0
      else:
        self.ver = struct.unpack("<H", list2str(r[:2]))[0]

      print "Firmware ver.%d, params size = %d" % (self.ver, self.psz)
      if (self.psz != PSZ[self.ver]):
        raise NameError, "Device v.%d returned parameters block of incorrect size %d" % (self.ver, self.psz)
      self.fmt = FMT[self.ver]

  def cmd(self, cmd, buf=0):
    ok=False
    r=()
    while not ok:
      try:
        if not type(buf) is int:
          self.devh.controlMsg(usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_OUT, cmd,buf,timeout=500)
        else:
          r=self.devh.controlMsg(usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_IN, cmd,buf,timeout=500)
        ok=True
      except usb.USBError as usberr:
        print "USBError:", usberr
        self.reconnect()
      except AttributeError:
        self.reconnect()
    return r

  def start(self):
    self.cmd(CMD_START)

  def single(self):
    self.cmd(CMD_SINGLE)

  def stop(self):
    self.cmd(CMD_STOP)

  def set_params(self,**p):
    params_list = ('t','n','t1','w','a');
    params_max = {
      't' : 0xffff if self.ver == 0 else 0xffffffff,
      'n' : 0xffff,
      't1': 0xffff,
      'w' : 0xffff,
      'a' : 0xffff,
    }

    for k in params_list:
      if not k in p.keys():
        raise NameError, "Not enough arguments: %s is missing" % k

    if (reduce(lambda a, b: a or b,
               map(lambda k: p[k] < 1 or p[k] > params_max[k],
                   params_list))):
      raise NameError, "Parameter(s) value(s) are out of bounds"

    if (p['n'] * p['t1'] > p['t'] or
        p['w'] > p['t1']):
      raise NameError, "Inconsistent parameters values"

    self.cmd(CMD_PARAMS, struct.pack(self.fmt, *map(lambda k: p[k], params_list)))

  def get_params(self):
    r = list2str(self.cmd(CMD_GETPARAMS, self.psz))
    return struct.unpack(self.fmt, r)

  def store(self):
    self.cmd(CMD_STORE)

  def load(self):
    self.cmd(CMD_LOAD)

  def trig_en(self):
    self.cmd(CMD_TRIG_EN)

  def trig_dis(self):
    self.cmd(CMD_TRIG_DIS)

if __name__=="__main__":
  from Tkinter import *
  from tkMessageBox import showerror,showinfo
  import tkFont, tkFileDialog
  from time import time,sleep
  import os.path

  active_input = None
  
  def set_active_input(event):
    global active_input
    active_input = event.widget.esl_input_name
    adjust_params(active_input)

  def adjust_params(event):
    global p_inputs, p_limits
    
    # get updated input name into k
    if type(event) is str:
      k=event
    else:
      k=event.widget.esl_input_name

    # input contents
    ptxt=p_inputs[k].get()

    # conjugated inputs dictionary
    ms2hz={'t':'1/t','1/t':'t','t1':'1/t1','1/t1':'t1'}

    if len(ptxt):
      # in input is not empty
      # adjust the value to fit in the bounds
      mn,mx,c,typ,fmt = map(lambda k1: p_limits[k][k1], ('min','max','c','typ','fmt'))
      pval=typ(ptxt)
      if pval < mn/c: pval=mn/c
      if pval > mx/c: pval=mx/c
      ptxt=fmt % pval
      p_inputs[k].set(ptxt)
      
      # set conjugate param value
      if k in ms2hz.keys():
        p_inputs[ms2hz[k]].set(p_limits[ms2hz[k]]['fmt'] % (1e3/pval))

    else:
      # if input is emty...
      if k in ms2hz.keys() and len(p_inputs[ms2hz[k]].get()):
        # ...set its value from conjugated input (if any)
        typ = p_limits[ms2hz[k]]['typ']
        v = typ(p_inputs[ms2hz[k]].get())
        p_inputs[k].set(p_limits[k]['fmt'] % (1e3 / v))

    return False

  def load(f):
    if os.path.isfile(f):
      fd=open(f)
      for s in fd:
        k,v=s.split()
        p_inputs[k].set(v)
      fd.close()

  def save(f):
    fd=open(f,'w')
    for k in p_inputs.keys():
      v=p_inputs[k].get()
      if not len(v): v="0"
      print >>fd, "%s %s"%(k,v)
    fd.close()

  def apply_params():
    global esl, p_inputs, p_limits

    if active_input:
      adjust_params(active_input)

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

  def quit():
    global esl,root
    esl.store()
    root.destroy()


  p_limits={'t':{'min':1,
                 'max':0xffff,
                 'label':'T, ms',
                 'c':ms2tick,
                 'typ':float,
                 "fmt":"%.2f"},
           'n':{'min':1,
                'max':0xffff,
                'label':'N',
                'c':1,
                'typ':int,
                "fmt":"%d"},
           't1':{'min':1,
                 'max':0xffff,
                 'label':'T1, ms',
                 'c':ms2tick,
                 'typ':float,
                 "fmt":"%.2f"},
           'w':{'min':1,
                'max':0xffff,
                'label':'w, ms',
                'c':ms2tick,
                'typ':float,
                "fmt":"%.2f"},
           'a':{'min':1,
                'max':1023,
                'label':'A, mV',
                'c':1/10.,
                'typ':float,
                "fmt":"%.0f"},
           '1/t':{'max':1./1,
                  'min':1./0xffff,
                  'label':'1/T, Hz',
                  'c':1e-3/ms2tick,
                  'typ':float,
                  "fmt":"%.2f"},
           '1/t1':{'max':1./1,
                   'min':1./0xffff,
                   'label':'1/T1, Hz',
                   'c':1e-3/ms2tick,
                   'typ':float,
                   "fmt":"%.2f"}
           }

  p_inputs={}

  try:
    esl=ESL(usestub=False)
  except NameError as e:
    showerror("ERROR", str(e))
    sys.exit(1)

  # adjust parameters limits
  if esl.ver == V1:
    p_limits['t']['max'] = 0xffffffff
    p_limits['1/t']['min'] = 1./p_limits['t']['max']

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
  Button(frMnu, text="Quit", command=quit).pack(side=LEFT)

  frInp=Frame(root)
  frInp.pack(side=TOP)

  frLabels=Frame(frInp)
  frLabels.pack(side=LEFT)
  frInputs=Frame(frInp)
  frInputs.pack(side=LEFT)
  frLims=Frame(frInp)
  frLims.pack(side=LEFT)

  for k in ('t','1/t','n','t1','1/t1','w','a'):
    mn,mx,label,confac,typ = map(lambda k1: p_limits[k][k1],
                                 ('min','max','label','c','typ'))
    Label(frLabels,text=label).pack(side=TOP,anchor='nw')
    vtxt=StringVar()
    en=Entry(frInputs, width=7, textvariable=vtxt)
    en.pack(side=TOP,anchor='nw')
    en.bind("<FocusOut>", adjust_params)
    en.bind("<FocusIn>", set_active_input)
    en.esl_input_name=k
    p_inputs[k]=vtxt
    Label(frLims,text=str(typ(round(mn/confac,2)))+" - "+str(typ(round(mx/confac,2))) ).pack(side=TOP,anchor='nw')


  frBut=Frame(root)
  frBut.pack(side=TOP)
  Button(frBut, text="Start", command=start).pack(side=LEFT)
  Button(frBut, text="Single", command=single).pack(side=LEFT)
  Button(frBut, text="Stop",command=esl.stop).pack(side=LEFT)
  Button(frBut, text="TrigON",command=esl.trig_en).pack(side=LEFT)
  Button(frBut, text="TrigOFF",command=esl.trig_dis).pack(side=LEFT)

  esl.load()
  r=esl.get_params()
  i2k=['t','n','t1','w','a']
  map(lambda i: p_inputs[i2k[i]].set(p_limits[i2k[i]]["fmt"] % (r[i]/p_limits[i2k[i]]['c'])), range(5))
  map(adjust_params, ('t', 't1'))

  root.mainloop()
