#!/usr/bin/python3
#
###############################################################################
#  
# bodeplot.py
#
# Usage: python3 bodeplot.py [-h] [--port PORT] [--fstart FSTART] 
#                   [--fstop FSTOP][--fstep FSTEP] [--filename FILENAME]
#
# Create and save a bodeplot using the FeelTech 3225 function generator and
# Hantek 6022 oscilloscope
#
# options:
#  -h, --help           show this help message and exit
#  --port PORT          Serial port for the function generator. Default
#                       /dev/ttyUSB0.
#  --fstart FSTART      Starting frequency for the bodeplot in Hz. Default 10
#                       Hz.
#  --fstop FSTOP        Stopping frequency for the bodeplot in Hz. Default 5
#                       MHz.
#  --fstep FSTEP        Step frequency multiplier. Default 1.1.
#  --filename FILENAME  Filename to save the bodeplot information. Default
#                       bodeplot.csv.
#
#
# Utilizes a FeelTech FY3225S function generator and a Hantek 6022 to sweep
# a filter from 10 Hz to 2.5 MHz and create a bode frequency response plot
# and save the plot information to 'bode.csv'. Channel 1 on the oscilloscope
# is the filter output and Channel 2 on the oscilloscope is the filter input
# (i.e. the function generator output).
#
# Depends on having the python-feeltech and Hantek6022API.
# https://github.com/atx/python-feeltech
# https://github.com/Ho-Ro/Hantek6022API
#
# Author: Jonathan Weaver, jonw0224@gmail.com
# Date: 10/6/2024
# Version: 
# 9/23/2024 - 1.00 - Created the file by following the examples for the libaries
# 9/30/2024 - 1.01 - Added arguments and argument parsing so the port, start
#                    frequency, stop frequency, frequency step, and save
#                    filename as arguments rather than hardcoded.
# 10/6/2024 - 1.02 - Added gain control to expand the gain range for the 
#                    bodeplot. Will use 10 Vpp down to 0.1 Vpp on the function
#                    generator and modify the scope channel gains to maximize
#                    the range of the bodeplot.
# 
# Copyright (C) 2024 Jonathan Weaver
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

# Imports and dependencies
import feeltech
from PyHT6022.LibUsbScope import Oscilloscope
import numpy as np
import matplotlib.pyplot as plt
import pylab
import time
import sys
import argparse
import math
import csv

# Declare Global Constants
channelHighGain = 10 # Channel Gain, 10 is the highest gain, used here for more precise measurements
channelLowGain = 1 # Channel Gain, 1 is the lowest gain, used here for when we need to use a higher magnitude input
lowerAmplitude = 0.1 # Usa a 0.1 V peak to peak sine wave with the function generator when the filter gain is more than 10
lowAmplitude = 1 # Use a 1 V peak to peak sine wave with the function generator when the filter gain is more than 1/200
highAmplitude = 10 #Use a 10 V peak to peak sine wave with the function generator when the filter gain is less than 1/200
samplerates = (20, 32, 50, 64, 100, 128, 200, 500, 1000, 2000, 4000, 8000, 10000) # Valid samplerates in kilo samples per second
blocks = 20 # Number of 1024 samples to capture

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser(
    prog='bodeplot.py',
    description='Create and save a bodeplot using the FeelTech 3225 function generator and Hantek 6022 oscilloscope' )
ap.add_argument( "--port", default = "/dev/ttyUSB0", help = "Serial port for the function generator. Default /dev/ttyUSB0." )
ap.add_argument( "--fstart", type = int, default=10, help = "Starting frequency for the bodeplot in Hz. Default 10 Hz." )
ap.add_argument( "--fstop", type = int, default = 5e6, help="Stopping frequency for the bodeplot in Hz. Default 5 MHz." )
ap.add_argument( "--fstep", type = float, default = 1.1, help="Step frequency multiplier. Default 1.1." )
ap.add_argument( "--filename", default = "bodeplot.csv", help="Filename to save the bodeplot information. Default bodeplot.csv." )

options = ap.parse_args()

# Setup Function Generator
ft = feeltech.FeelTech(options.port)
c = ft.channels()
 
# Create place to hold data from the Oscilloscope capture
data_points = blocks * 1024

# Skip the first 2K samples due to unstable transfer from oscilloscope
skip = 2 * 1024
data_points += skip

# Setup Oscilloscope
scope = Oscilloscope()
scope.setup()
scope.open_handle()

# Upload correct firmware into device's RAM
if (not scope.is_device_firmware_present):
    scope.flash_firmware()

# Scope configuration
scope.set_num_channels(2) # Two channels
# Setup channel 1
scope.set_ch1_voltage_range(channelHighGain) # Highest Gain
scope.set_ch1_ac_dc(scope.DC) # DC coupling
# Setup channel 2
scope.set_ch2_voltage_range(channelHighGain) # Highest Gain
scope.set_ch2_ac_dc(scope.DC) # DC coupling

# Start frequency
freq = options.fstart

# Save bodeplot data
data = []

# Default Gain mode
gainMode = 1

while(freq < options.fstop):
    # Calculate the sample rate to use for the scope
    samplerate_target = 2*freq
    samplerate = samplerates[0]
    for sr in samplerates:
        if samplerate < samplerate_target:
            samplerate = sr
    # Calculate and set the sample rate ID from real sample rate value
    if samplerate < 1e3:
        sample_id = int( round( 100 + samplerate / 10 ) ) # 20k..500k -> 102..150
    else:
        sample_id = int( round( samplerate / 1e3 ) ) # 1000k -> 1
    scope.set_sample_rate(sample_id)

    # Set the function generator waveform
    if gainMode == 0:
        scope.set_ch1_voltage_range(channelHighGain) # Highest Gain
        scope.set_ch2_voltage_range(channelLowGain) # Lowest Gain
        c[0].frequency(freq).waveform(feeltech.SINE).offset(0).amplitude(highAmplitude) # 10 Vpp
    elif gainMode == 1:
        scope.set_ch1_voltage_range(channelHighGain) # Highest Gain
        scope.set_ch2_voltage_range(channelHighGain) # Highest Gain
        c[0].frequency(freq).waveform(feeltech.SINE).offset(0).amplitude(lowAmplitude) # 1 Vpp
    elif gainMode == 2:
        scope.set_ch1_voltage_range(channelLowGain) # Lowest Gain
        scope.set_ch2_voltage_range(channelHighGain) # Highest Gain
        c[0].frequency(freq).waveform(feeltech.SINE).offset(0).amplitude(lowAmplitude) # 1 Vpp
    else:
        scope.set_ch1_voltage_range(channelLowGain) # Lowest Gain
        scope.set_ch2_voltage_range(channelHighGain) # Highest Gain
        c[0].frequency(freq).waveform(feeltech.SINE).offset(0).amplitude(lowerAmplitude) # 0.1 Vpp


    # Read and apply scope calibration values
    calibration = scope.get_calibration_values()
    
    # Wait a 10th of a second for things to settle out with the function generator and scope
    time.sleep(0.1)

    # Capture the waveforms on channel 1 and channel 2
    ch1_data, ch2_data = scope.read_data(data_points)#,raw=True)#timeout=1)
    if gainMode == 0:
        voltage_data1 = scope.scale_read_data(ch1_data[skip:], channelHighGain, channel=1 )
        voltage_data2 = scope.scale_read_data(ch2_data[skip:], channelLowGain, channel=2 )
    elif gainMode == 1:
        voltage_data1 = scope.scale_read_data(ch1_data[skip:], channelHighGain, channel=1 )
        voltage_data2 = scope.scale_read_data(ch2_data[skip:], channelHighGain, channel=2 )
    else
        voltage_data1 = scope.scale_read_data(ch1_data[skip:], channelLowGain, channel=1 )    
        voltage_data2 = scope.scale_read_data(ch2_data[skip:], channelHighGain, channel=2 )

    timing_data, rate_label = scope.convert_sampling_rate_to_measurement_times(data_points-skip, sample_id)

    # Calculate the RMS value and DC value
    rms1 = 0
    dc1 = 0
    n1 = 0
    for v in voltage_data1:
        rms1 = rms1 + v*v
        dc1 = dc1 + v
        n1 = n1 + 1
    rms1 = math.sqrt(rms1/n1) - dc1/n1

    # Calculate the RMS value and DC value
    rms2 = 0
    dc2 = 0
    n2 = 0
    for v in voltage_data2:
        rms2 =rms2 + v*v
        dc2 = dc2 + v
        n2 = n2 + 1
    rms2 = math.sqrt(rms2/n2) - dc2/n2

    # If the gain is small, do it over again at a higher resolution
    if gainMode == 0 and rms1 > 0.2:
        gainMode = 1
    # If the gain is high, but set for small, do it over gain at a lower resolution
    elif gainMode == 1 and rms1 < 0.015:
        gainMode = 0
    elif gainMode == 1 and rms1 > 0.4:
        gainMode = 2
    elif gainMode == 2 and rms1 < 0.15:
        gainMode = 1
    elif gainMode == 2 and rms1 > 4:
        gainMode = 3
    elif gainMode == 3 and rms1 < 0.15:
        gainMode = 2
    else:
        # Compute the FFT for Channel 1
        fft_values = np.fft.fft(voltage_data1)
        N = len(voltage_data1)  # Number of samples
        frequencies = np.fft.fftfreq(N, 1/samplerate/1000)  # Frequency bins

        # Compute the magnitude and phase of the FFT
        fft_magnitude = np.abs(fft_values)[:N // 2] / N  # Magnitude (positive frequencies)
        fft_phase = np.angle(fft_values)[:N // 2]  # Phase (positive frequencies)
        frequencies = frequencies[:N // 2]  # Positive frequency range

        # Find the index of the fundamental frequency (largest magnitude component)
        fundamental_index = np.argmax(fft_magnitude[1:]) + 1  # Skip the DC component (index 0)

        # Fundamental frequency, magnitude, and phase
        fundamental_frequency = frequencies[fundamental_index]
        fundamental_magnitude = fft_magnitude[fundamental_index]
        fundamental_phase = fft_phase[fundamental_index]

        # Compute the FFT for Channel 2
        fft_values = np.fft.fft(voltage_data2)
        N = len(voltage_data2)  # Number of samples
        frequencies = np.fft.fftfreq(N, 1/samplerate/1000)  # Frequency bins

        # Compute the magnitude and phase of the FFT
        fft_magnitude = np.abs(fft_values)[:N // 2] / N  # Magnitude (positive frequencies)
        fft_phase = np.angle(fft_values)[:N // 2]  # Phase (positive frequencies)
        frequencies = frequencies[:N // 2]  # Positive frequency range

        # Find the index of the fundamental frequency (largest magnitude component)
        fundamental_index = np.argmax(fft_magnitude[1:]) + 1  # Skip the DC component (index 0)

        # Fundamental frequency, magnitude, and phase
        fundamental_frequency2 = frequencies[fundamental_index]
        fundamental_magnitude2 = fft_magnitude[fundamental_index]
        fundamental_phase2 = fft_phase[fundamental_index]
    
        # Calculate the phase difference
        deltaphase = fundamental_phase - fundamental_phase2
        if deltaphase > math.pi:
            deltaphase = deltaphase - 2*math.pi
        if deltaphase < -math.pi:
            deltaphase = deltaphase + 2*math.pi

        # Save the bode plot data
        data.append([freq, rms1, rms2, rms1/rms2, deltaphase])    

        # Next frequency
        freq = freq*options.fstep

# Close the scope
scope.close_handle()

# Save the bodeplot data as a CSV file
with open(options.filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Frequency", "Channel 1 RMS Magnitude", "Channel 2 RMS Magnitude", "Gain (Ch1/Ch2)", "Phase Difference"])
    writer.writerows(data)

# Extract the bodeplot data for plotting
data_array = np.array(data)
frequencies = data_array[:,0]
gains = data_array[:,3]
phase = data_array[:,4]*180/math.pi

# Create a figure and two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7))  # 2 rows, 1 column

# Create a log-log plot for the magnitude
ax1.loglog(frequencies, gains, marker='o')  # Use log-log scale

# Add labels and title
ax1.set_title("Magnitude Frequency Response")
# ax1.set_xlabel("Frequency in Hz (log scale)")
ax1.set_ylabel("Gain Magnitude (log scale)")

# Show grid
ax1.grid(True, which="both", linestyle="--", linewidth=0.5)

# Create a semi-log plot for the phase
ax2.semilogx(frequencies, phase, marker='o', color='blue')  # Semilog y-axis

# Add labels and title
ax2.set_title("Phase Frequency Response")
ax2.set_xlabel("Frequency in Hz (log scale)")
ax2.set_ylabel("Phase Shift in Degrees")

# Show grid
ax2.grid(True, which="both", linestyle="--", linewidth=0.5)

# Display the plot
plt.show()

