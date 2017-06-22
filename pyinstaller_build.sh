#!/bin/bash

pyinstaller --onefile --windowed --icon=pyinstaller_resources/pumpyouup.icns PumpYouUp.py

cp -Rp dist/PumpYouUp.app .
sudo cp -Rp dist/PumpYouUp.app /Applications

