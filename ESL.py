import usb, struct
ms2tick = 12e3/256

class ESL:
  idVendor = 0x16c0
  idProduct = 0x05dc
  Manufacturer = "piton"
  Product = "ESL"

  def __init__(self):
    self.devh=None
    for bus in usb.busses():
      for dev in bus.devices:
        if dev.idVendor == self.idVendor and dev.idProduct == self.idProduct:
          devh = dev.open()
          if devh.getString(dev.iManufacturer, len(self.Manufacturer)) == self.Manufacturer and  devh.getString(dev.iProduct, len(self.Product)) == self.Product:
            self.devh = devh
            print "Device found."
    if not self.devh: raise NameError, "Device not found"

  def start(self):
     self.devh.controlMsg(usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_IN, 1, 0)

  def stop(self):
     self.devh.controlMsg(usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_IN, 0, 0)

  def set_params(self,t,n,t1,w,amp):
    self.devh.controlMsg(usb.TYPE_VENDOR | usb.RECIP_DEVICE | usb.ENDPOINT_OUT, 2,\
      struct.pack("<hhhhh", ms2tick*t, n , ms2tick*t1, ms2tick*w, amp))
if __name__=="__main__":
  from Tkinter import *

  root=Tk()
  root.title("ElectroStimuLator")
  root.resizable(0,0)

  frInp=Frame(root)
  frInp.pack(side=TOP)
  frBut=Frame(root)
  frBut.pack(side=TOP)

  frLabels=Frame(frInp)
  frLabels.pack(side=LEFT)
  frInputs=Frame(frInp)
  frInputs.pack(side=LEFT)
 
  Label(frLabels,text="T, ms").pack(side=TOP,anchor='nw')
  enT=Entry(frInputs)
  enT.pack(side=TOP,anchor='nw')
 
  Label(frLabels,text="N").pack(side=TOP,anchor='nw')
  enN=Entry(frInputs)
  enN.pack(side=TOP,anchor='nw')

  Label(frLabels,text="T1, ms").pack(side=TOP,anchor='nw')
  enT1=Entry(frInputs)
  enT1.pack(side=TOP,anchor='nw')

  Label(frLabels,text="w, ms").pack(side=TOP,anchor='nw')
  enW=Entry(frInputs)
  enW.pack(side=TOP,anchor='nw')

  Label(frLabels,text="A, mV").pack(side=TOP,anchor='nw')
  enA=Entry(frInputs)
  enA.pack(side=TOP,anchor='nw')
  
  Button(frBut, text="Apply",command=lambda x=1: 1).pack(side=LEFT)
  Button(frBut, text="Start").pack(side=LEFT)
  Button(frBut, text="Single").pack(side=LEFT)
  Button(frBut, text="Stop").pack(side=LEFT)
  root.mainloop()
