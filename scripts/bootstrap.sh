#!/bin/bash
sudo python3 -m pip install --ignore-installed \
    "numpy<2.0" \
    pandas \
    Pillow \
    pyarrow \
    tensorflow-cpu==2.13.0
