## This project is not tested as of now and is very likely to contain bugs and exploits. Use it for study or research

## Overview
A webmin like website written with django, django-channels, django-otp, 
bootstrap, xterm.js, chart.js etc.

Current implemented functionality: 
- web terminal
- file manager
  - Only manage files under FILE_MANAGER_ROOT_PATH in settings.py
  - Browse, move, create and delete folder and file
  - Upload file.
  - File download, current using synchronous open(), which means the file will be fully consumed before serving. trying to find an async solution
  - file rename is done via the move function. the behavior should be the same as the linux 'mv'

- dashboard with basic system info, charts currently not implemented.

## Compatibility
The project is tested on ubuntu 22.04 but should ideally work on most Linux distros

Python version 3.11 and above. Should work for lower version of python if you swap 
"termios.tcsetwinsize" with commented out code "set_winsize". (Maybe I should do a version checking)
## Setup
- Clone project and install requirements.txt, the project comes with a migrated sqlite database.
- Install and setup redis-server 
  - on ubuntu run: sudo apt install redis-server
  - then edit /etc/redis/redis.conf. Modify "supervised no" to "supervised systemd"
  - restart redis service. it should run on port 6379 by default

- HTTPS
  - Install and setup caddy with Caddyfile in the project root for https and other functionalities.
  - If you don't want https and just want to test the project, remove the last 4 lines in settings.py 

## Coding detail
Web terminal is implemented with websocket, frontend is xterm.js. Backend is implemented with pty.fork()
pseudo terminal. User login with "su --loign"

File manager operations are done with websocket. File upload using ajax and http.

Modified django-otp to separate login and otp page and add support for websocket.