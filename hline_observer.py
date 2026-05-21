#!/usr/bin/env python3
"""
H-Line Observer — Live 21 cm hydrogen line spectrometer
=======================================================
Hardware: Nooelec NESDR Smart (RTL-SDR) + Nooelec Lana LNA
Center frequency: 1420.405 MHz
Bandwidth: 2.048 MHz (2.048 MSPS)
FFT size: 4096 bins (~500 Hz/bin)

Controls:
    s — Save current averaged spectrum as FITS
    r — Reset the running average
    q — Quit

Dependencies:
    pip install pyrtlsdr numpy matplotlib astropy
"""

import sys
import time
import datetime
import os
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from astropy.io import fits
from scipy.integrate import trapezoid
from rtlsdr import RtlSdr
import argparse

# ─────────────────────── RTL-SDR Setup ───────────────────────
def init_sdr(args):
    """Initialize RTL-SDR with max gain at 1420.405 MHz."""
    
    sdr = RtlSdr()
    "TODO: figure out why sample rate is the same as band width for SDR is it double sideband perhaps?"
    sdr.sample_rate = args.bandwidth*1e3
    sdr.center_freq = args.freq*1e6

    # Set gain to maximum available
    gains = sdr.valid_gains_db
    sdr.set_manual_gain_enabled(True)
    sdr.gain = args.gain
    print(f"SDR initialized:")
    print(f"  Center freq : {sdr.center_freq / 1e6:.3f} MHz")
    print(f"  Sample rate : {sdr.sample_rate / 1e6:.3f} MSPS")
    print(f"  Gain        : {sdr.gain} dB (of {gains})")
    print(f"  FFT size    : {args.nfft} bins")
    print(f"  Freq res    : {sdr.sample_rate / args.nfft:.1f} Hz/bin")
    print(f"  Averaging   : {args.nsamples} spectra per update")
    return sdr


# ─────────────────── Spectrum Computation ────────────────────
def compute_averaged_spectrum(sdr, args):
    """Read IQ samples, FFT, square, and average ``args.nsamples`` integrations.

    See lab manual §4.1 (The Readout) for the full description.

    Parameters
    ----------
    sdr : RtlSdr
        Initialised SDR (from ``init_sdr``).
    args : argparse.Namespace
        Uses ``args.nfft`` (FFT size), ``args.nsamples`` (averages per update),
        ``args.bandwidth`` (kHz), ``args.freq`` (centre frequency in MHz).

    Returns
    -------
    freqs_mhz : ndarray, shape (args.nfft,)
        Frequency axis in MHz, centred on ``args.freq``, spanning ``args.bandwidth``/1000 MHz.
    psd_db : ndarray, shape (args.nfft,)
        Averaged power spectrum, dB scale, for the live plot.
    psd_linear : ndarray, shape (args.nfft,)
        Averaged power spectrum, linear scale, used for the integrated total-power panel
        and for the FITS log.
    """
    # TODO: window the IQ samples (Hann), FFT them, square the magnitude, accumulate
    # args.nsamples spectra, divide, convert to dB, and build the frequency axis.
    # See lab manual §4.1.
    raise NotImplementedError(
        "compute_averaged_spectrum: TODO — see lab manual §4.1"
    )


# ──────────────────── FITS File Saving ───────────────────────
def save_fits(freqs, metadata, sdr, args):
    """Write the buffered spectra of this logging run to a FITS file.

    On-disk schema (must match what the analysis notebook's ``load_fits`` expects):

        Primary HDU : frequency axis in MHz, shape (nfft,)
        SPECTRUM    : binary-table extension, one row per averaged spectrum,
                      columns TIME (UNIX timestamp, float) and PSD (linear power,
                      shape (nfft,))

    Path: ``{args.dir}/hline_YYYYMMDD_HHMMSS.fits`` with the UTC timestamp of the flush.
    See lab manual §4.1 for the full description.

    Parameters
    ----------
    freqs : ndarray, shape (nfft,)
        Frequency axis in MHz (from ``compute_averaged_spectrum``).
    metadata : numpy.recarray
        Record array with fields TIME and PSD, one record per buffered spectrum.
    sdr, args : as elsewhere in this file.

    Returns
    -------
    fpath : str
        Path of the file just written.
    """
    # TODO: use astropy.io.fits to build the Primary HDU + SPECTRUM binary-table extension
    # described above, then write to {args.dir}/hline_YYYYMMDD_HHMMSS.fits.
    # See lab manual §4.1.
    raise NotImplementedError(
        "save_fits: TODO — see lab manual §4.1"
    )


# ──────────────────── Live Plot ──────────────────────────────
def main():

    parser = argparse.ArgumentParser(description = 'Wok Telescope Data Aquisition System')

    parser.add_argument('--freq',
                        type=float,
                        default=1421.0,
                        help = 'Center frequency in MHz')
    
    parser.add_argument('--bandwidth',
                        type=int,
                        default=2048,
                        help = 'Bandwidth in kHz')
    parser.add_argument('--nfft',
                        type=int,
                        default=4096,
                        help = 'Number of spectral channels')
    parser.add_argument('--nsamples',
                        type=int,
                        default=100,
                        help='Number of temporal samples per sectrum')
    parser.add_argument('--gain',
                        type=float,
                        default=20.7,
                        help='SDR gain max: 49.6 dB')
    parser.add_argument('--dir',
                        type=type('hline_data'),
                        default='hline_data',
                        help='Directory to store the data in')
    parser.add_argument('--mode',
                        type=type('night'),
                        default='night',
                        help='Color mode options are "day" and "night" ')
    try:
        args=parser.parse_args()
    except argparse.ArgumentError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    
    sdr = init_sdr(args)

    # Initial spectrum for plot setup
    last_save = datetime.datetime.now().timestamp()
    write_index = 0
    spec_data=[]
    int_power=np.ones(500)*np.nan
    tstamps=np.ones(500)*np.nan
    is_saving = 0
    freqs, psd_db, psd_linear = compute_averaged_spectrum(sdr, args)
    int_power[write_index] = trapezoid(psd_linear,x=freqs)
    tstamps[write_index] = datetime.datetime.now().timestamp()
    write_index += 1
    
    if is_saving == 1:
        spec_data.append((datetime.datetime.now().timestamp(),psd_linear))

    # --- Matplotlib setup ---
    if(args.mode=='night'):
        line_color = "#00d4ff"
        text_color = "white"
        face_color = "#16213e"
        fig_facecolor = "#1a1a2e"
        status_color = "#00ff88" 
    else:
        line_color = "#0011ff"
        text_color = "black"
        face_color = "#ffffff"
        fig_facecolor = "#FFFFFF"
        status_color = "#ff0000"
    fig = plt.figure(figsize=(12, 6))
    fig.patch.set_facecolor(fig_facecolor)
    
    ax1=fig.add_subplot(2,1,1)
    ax2=fig.add_subplot(2,1,2)
    ax1.set_facecolor(face_color)
    ax2.set_facecolor(face_color)
    good = np.where(np.isnan(int_power))
    (line,) = ax1.plot(freqs, psd_db, color=line_color, linewidth=0.8, alpha=0.9)
    (line2,) = ax2.plot(tstamps[good],int_power[good], color=line_color, linewidth=0.8, alpha=0.9)
    # Mark the H-line rest frequency
    ax1.axvline(x=1420.405, color="#ff6b6b", linestyle="--", alpha=0.7, label="HI rest freq")

    ax1.set_xlabel("Frequency (MHz)", color=text_color, fontsize=12)
    ax1.set_ylabel("Power (dB)", color=text_color, fontsize=12)
    ax2.set_xlabel("UNIX Time (s)", color=text_color, fontsize=12)
    ax2.set_ylabel("Power (arb.)", color=text_color, fontsize=12)
    ax2.set_xlim((datetime.datetime.now().timestamp()-60,datetime.datetime.now().timestamp()))

    ax1.set_title("Live Spectrum", color=text_color, fontsize=14)
    ax2.set_title("Total power", color=text_color, fontsize=14)
    ax1.tick_params(colors=text_color)
    ax2.tick_params(colors=text_color)
    ax1.legend(loc="upper right", facecolor=face_color, edgecolor=text_color, labelcolor=text_color)
    ax1.grid(True, alpha=0.2, color=text_color)
    ax2.grid(True, alpha=0.2, color=text_color)
    status_text = ax1.text(
        0.01, 0.97, "", transform=ax1.transAxes,
        color=status_color, fontsize=9, verticalalignment="top",
        fontfamily="monospace",
    )

    plt.tight_layout()

    # --- State ---
    state = {"running": True, "save_count": 0}

    # --- Key handler ---
    def on_key(event):
        nonlocal is_saving,spec_data
        if event.key == "s":
            if is_saving == 0:
                is_saving = 1
                last_save = datetime.datetime.now().timestamp()
                print("Started data logging")
            else:
                is_saving =0
                #save and clear buffer
                metadata = np.rec.array(spec_data,dtype=[('TIME',type(spec_data[0][0])),('PSD',type(spec_data[0][1]))])
                save_fits(freqs,metadata,sdr,args)
                spec_data=[]
                last_save = datetime.datetime.now().timestamp()
                state["save_count"] += 1
                print("Stopped data logging")
        elif event.key == "r":
            print("\n  ↻ Average reset (takes effect on next update)")
        elif event.key == "q":
            if is_saving ==1:
                metadata = np.rec.array(spec_data,dtype=[('TIME',type(spec_data[0][0])),('PSD',type(spec_data[0][1]))])
                save_fits(freqs,metadata,sdr,args)
                spec_data=[]
                is_saving = 0
                state["save_count"] += 1
                print("Stopped data logging")
            state["running"] = False
            plt.close("all")

    fig.canvas.mpl_connect("key_press_event", on_key)

    # --- Animation update ---
    def update(frame):
        nonlocal freqs, psd_db, psd_linear, spec_data,last_save,write_index
        if not state["running"]:
            return (line,)

        freqs, psd_db, psd_linear = compute_averaged_spectrum(sdr, args)
        if write_index >= 500:
            write_index =0
        
        int_power[write_index] = trapezoid(psd_linear,x=freqs)
        tstamps[write_index] = datetime.datetime.now().timestamp()
        write_index+=1 
        line.set_ydata(psd_db)
        if np.sum(np.isnan(int_power)) == 0:
            sorted = np.argsort(tstamps)
            line2.set_xdata(tstamps[sorted])
            line2.set_ydata(int_power[sorted])
        else:
            line2.set_xdata(tstamps)
            line2.set_ydata(int_power)
        if is_saving ==1:
            spec_data.append((datetime.datetime.now().timestamp(),psd_linear))
            if (datetime.datetime.now().timestamp() - last_save) > 300:
                metadata = np.rec.array(spec_data,dtype=[('TIME',type(spec_data[0][0])),('PSD',type(spec_data[0][1]))])
                save_fits(freqs,metadata,sdr,args)
                spec_data=[]
                last_save = datetime.datetime.now().timestamp()
                state["save_count"] += 1
        # Auto-scale y-axis with some margin
        ymin1, ymax1 = psd_db.min(), psd_db.max()
        margin = (ymax1 - ymin1) * 0.1 if ymax1 > ymin1 else 1
        ax1.set_ylim(ymin1 - margin, ymax1 + margin)
        ymin2, ymax2 = np.nanmin(int_power), np.nanmax(int_power)
        margin = (ymax2 - ymin2) * 0.1 if ymax2 > ymin2 else 1
        ax2.set_ylim(ymin2 - margin, ymax2 + margin)
        ax2.set_xlim((datetime.datetime.now().timestamp()-60,datetime.datetime.now().timestamp()))
        now = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
        status_text.set_text(
            f"Time: {now}  |  Gain: {sdr.gain} dB  |  "
            f"Avg: {args.nsamples}  |  Saved: {state['save_count']}  |  "
            f"[S]ave  [R]eset  [Q]uit"
        )
        return (line,line2)

    ani = FuncAnimation(fig, update, interval=50, blit=False, cache_frame_data=False)

    print("\n  Live plot running. Focus the plot window and use keyboard shortcuts.")
    print("  [S] Save FITS  |  [R] Reset average  |  [Q] Quit\n")

    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        if is_saving ==1:
            metadata = np.rec.array(spec_data,dtype=[('TIME',type(spec_data[0][0])),('PSD',type(spec_data[0][1]))])
            save_fits(freqs,metadata,sdr,args)
            spec_data=[]
            state["save_count"] += 1
            print("Stopped data logging")
        sdr.close()
        print("SDR closed. Done.")


if __name__ == "__main__":
    main()
