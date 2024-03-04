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

Python version 3.11 and above. Should work with lower version of python if you swap 
"termios.tcsetwinsize" with commented out code "set_winsize" (in xterm/consumers.py). (Maybe I should do a version checking)
## Setup
- Clone project and install requirements.txt, the project comes with a migrated sqlite database.
- Install and setup redis-server 
  - on ubuntu run: sudo apt install redis-server
  - then edit /etc/redis/redis.conf. Modify "supervised no" to "supervised systemd"
  - restart redis service. it should run on port 6379 by default

- HTTPS
  - Install and setup caddy with Caddyfile in the project root for https and other functionalities.
  - If you don't want https, remove the last 4 lines in settings.py

- Login
  - if you are using the project database, the superuser account is username: admin, password: test_admin
  - Otp for admin account is "otpauth://totp/admin?secret=IHG2JGXILTOO273VJ2VX5V2HJ4ER5KDG&algorithm=SHA1&digits=6&period=30"
 or scan the qrcode below using the authenticator app. When prompting otp, choose the "Microsoft Auth" otp device.
Make sure the server time and authenticator device time are both accurate for it to work properly.
  
  ![Alt text](./imgs/localhost.svg)

## Coding detail
Web terminal is implemented with websocket, frontend is xterm.js. Backend is implemented with pty.fork()
pseudo terminal. User login with "su --loign"

File manager operations are done with websocket. File upload using ajax and http. File download with http.

Modified django-otp to separate login and otp page and added support for authentication with websocket.