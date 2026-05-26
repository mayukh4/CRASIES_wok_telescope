# CRASIES Wok Telescope

Software and example data for the wok-tenna 21 cm hydrogen-line lab activity at the CRASIES summer school.

## Hardware

- Nooelec NESDR Smart RTL-SDR
- Nooelec Lana LNA
- Wok dish with a dipole feed on an alt-az tripod

## Install

```bash
pip install pyrtlsdr numpy matplotlib astropy scipy
```

## Run

```bash
python3 hline_observer.py
```

Defaults: 1421 MHz centre, 2.048 MHz bandwidth, 4096 bins, 100-spectrum averaging, 20.7 dB gain. Run `python3 hline_observer.py --help` for the full flag list.

Keyboard controls (the Matplotlib window must have focus):

- `s` — start / stop FITS logging into `--dir` (default `hline_data/`)
- `q` — quit (flushes any unsaved data first)

## Files

| File | Purpose |
| --- | --- |
| `hline_observer.py` | Live readout. `compute_averaged_spectrum` and `save_fits` are TODOs — see lab manual §4.1. |
| `hline_analysis.ipynb` | Quick-look + science analysis notebook. Helper bodies and workflow cells are TODOs — see lab manual §4.2 and §7. |
| `data_2026_05_07/` | Example FITS files from 7 May 2026: a calibration scan and a target pointing at elevation 30°, azimuth 225°. Use this to test your pipeline before observing. |

## Troubleshooting

### macOS: `ImportError: Error loading librtlsdr`

`pyrtlsdr` is just the Python wrapper; you also need the native library:

```bash
brew install librtlsdr
```

If you then get a dyld error like `mach-o file, but is an incompatible architecture (have 'arm64', need 'x86_64')` on an Apple Silicon Mac, your Python is an Intel build (typical of older Anaconda installs) running under Rosetta. Homebrew gave you the correct arm64 `librtlsdr.dylib`, but the Intel Python can't load it. Two options below — the first leaves your existing Python and conda untouched, the second is the recommended long-term fix.

**Lightweight fix — install a Rosetta Homebrew alongside your arm64 one.** This gives you an x86_64 `librtlsdr.dylib` at `/usr/local/lib/`, which your Intel Python's dyld search list already includes. The two Homebrews live at separate prefixes (`/usr/local/` for x86, `/opt/homebrew/` for arm64) and don't conflict:

```bash
arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
arch -x86_64 /usr/local/bin/brew install librtlsdr
```

**Long-term fix — switch to a native arm64 Python via [Miniforge](https://github.com/conda-forge/miniforge).** Running Intel Python under Rosetta on Apple Silicon is slow and other C-extension libraries beyond `librtlsdr` will keep biting you. If you'll be doing scientific Python on this machine going forward, this is the cleaner answer:

```bash
brew install --cask miniforge
conda init "$(basename "${SHELL}")"
```

Open a new terminal so the init takes effect, then make a fresh environment:

```bash
conda create -n wok_tel python=3.12
conda activate wok_tel
pip install pyrtlsdr numpy matplotlib astropy scipy
```

`python3 -c "import platform; print(platform.machine())"` should now print `arm64`, and `from rtlsdr import RtlSdr` should import cleanly.

## Lab manual

Linked here once published.

## Reference

Fung et al. 2023, [arXiv:2309.15163](https://arxiv.org/abs/2309.15163).

## License

MIT — see [LICENSE](LICENSE).
