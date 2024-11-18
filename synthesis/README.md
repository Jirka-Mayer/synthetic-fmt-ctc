# Training data synthesis

This folder contains scripts that generate the synthetic training data.

The python files here have dependencies listed in the `requirements.txt` file.


## After cloning

> **Note:** All commands should be run in this `synthesis` sub-folder.

Create the virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt
```

Put the `fmt.tgz` file directly inside the `data` folder. Then unpack the FMT dataset:

```bash
.venv/bin/python3 -m app.unpack_fmt_dataset
```

Download the PrIMuS dataset (273.6 MB):

```
wget -P ../data/ https://grfia.dlsi.ua.es/primus/packages/primusCalvoRizoAppliedSciences2018.tgz
```

Install musescore:

```
make install-musescore
```
