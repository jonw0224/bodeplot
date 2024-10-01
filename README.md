# Bodeplot #

Create and save a bodeplot using the FeelTech 3225 function generator and
Hantek 6022 oscilloscope

Usage:

**python3 bodeplot.py [-h] [--port PORT] [--fstart FSTART]** 
                  **[--fstop FSTOP][--fstep FSTEP] [--filename FILENAME]**
                  
 options:
 
  -h, --help           show this help message and exit
  
  --port PORT          Serial port for the function generator. Default
                       /dev/ttyUSB0.
                       
  --fstart FSTART      Starting frequency for the bodeplot in Hz. Default 10
                       Hz.
                       
  --fstop FSTOP        Stopping frequency for the bodeplot in Hz. Default 5
                       MHz.
                       
  --fstep FSTEP        Step frequency multiplier. Default 1.1.
  
  --filename FILENAME  Filename to save the bodeplot information. Default
                       bodeplot.csv.


Utilizes a FeelTech FY3225S function generator and a Hantek 6022 oscillosope to sweep a filter from fstart to fstop by fstep and create a bode frequency response plot, display the plot, and save the plot information to 'bodeplot.csv'. Channel 1 on the oscilloscope is the filter output and Channel 2 on the oscilloscope is the filter input (i.e. the function generator Channel 1 output).

Depends on having python-feeltech and Hantek6022API installed.

https://github.com/atx/python-feeltech

https://github.com/Ho-Ro/Hantek6022API
