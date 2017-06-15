# PumpYouUp

Python app to control an NE500 device.
Refill pumps each day.
Code here generates a Python app.

## Testing

There are python unit tests in test_ne500_behavpump.py

## Installing

- Use pyinstaller_build.sh to create PumpYouUp.app in ./dist/
- Copy to /Applications: ````cp -R dist/PumpYouUp.app /Applications/````
- Use tmux-cssh-all to copy to all:
````
scp -rp histedrigtest.local:/Applications/PumpYouUp.app /Applications/
```

## TODO

Code should probably be refactored into a package and files/tests put in appropriate directories

## Contact

Mark Histed mhisted@gmail.com

Orig UI design: Leo Mitchell
