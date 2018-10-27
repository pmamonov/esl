# Firmware/API/GUI for x-SLON

This software is designed for work with [x-SLON devices](https://github.com/comcon1/x-SLON).  

Device is very small and is assembled simply. Please consult [assembly.txt](case/assembly.txt).

The GUI and the library lives in a single file _ESL.py_. 

**Control software _guiSLON_**

The main window of _guiSLON_ is shown in the Figure. The program has a simple interface and allows 
a user to set a pulse period, pulse width, number of pulses per train and train period.
The user can select between single pulse train and periodic pulse trains by pressing either the “Single” or the "Start" button.

![GUI window](slon_soft.jpg)

**Stimulation API**

The stimulation class _ESL_ is defined in _ESL.py_.

    from ESL import ESL, ms2tick
    esl = ESL()

One must define stimulation parameters before run:

    p = {
        't':	200 * ms2tick,
        'n':	1,
        't1':	200 * ms2tick,
        'w':	1 * ms2tick,
        'a':	1,
    }
    esl.set_params(**p)
    
And then run continuous stimulation:

    esl.start()
    time.sleep(10)
    esl.stop()

.. or single pulse:

    esl.single()
    
Example programs are supplemented:

- _esl\_single.py_ : Continuos stimulation
- _esl\_periodic.py_ : Periodic single stimulation
- _pedal.py_ : Stimulation by an external pulse
    
# Authors

Ilya Kuzmin <kuzmin.ilya@gmail.com>  
Peter Mamonov <pmamonov@gmail.com>  
Alexey Nesterenko <comcon1@protonmail.com>  

# Licensing

_usbdrv_ is a third-party library needed for firmware compilation.

"Firmware/API/GUI for x-SLON" project (P. Mamonov, I. Kuzmin, A. Nesterenko)
is released under 3-clause BSD license.
