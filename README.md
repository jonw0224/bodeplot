Usage:

**python3 bodeplot.py**

Utilizes a FeelTech FY3225S function generator and a Hantek 6022 oscillosope to sweep a filter from 10 Hz to 2.5 MHz and create a bode frequency response plot, display the plot, and save the plot information to 'bode.csv'. Channel 1 on the oscilloscope is the filter output and Channel 2 on the oscilloscope is the filter input (i.e. the function generator output).

Depends on having the python-feeltech and Hantek6022API.

https://github.com/atx/python-feeltech

https://github.com/Ho-Ro/Hantek6022API
