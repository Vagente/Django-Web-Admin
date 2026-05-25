## This project is only partially tested and may contain exploits. Use it for study or research

## Overview
A webmin like website written with django, django-channels, django-otp.
Frontend uses bootstrap, xterm.js, etc.

Current implemented functionality: 
- web terminal that allows login as different user with su
- file manager
  - Only manage files under FILE_MANAGER_ROOT_PATH in settings.py
  - Browse, move, create and delete folder and file
  - Upload file.
  - File download, current using synchronous open(), which means the file will be fully consumed before serving.
  - file rename is done via the move function. the behavior should be the same as the linux 'mv'

- dashboard with basic system info.
- journalctl log display

## Compatibility
Should compatible with most modern Linux distro, tested on Debian 13, Arch. 

## Setup
- Clone project and setup env.
- Install and setup valkey or redis(disable redis in settings.py if you don't want this)
- Change the root folder for file manager in settings.py
- Run the following in project root.
  ```shell
  python manage.py migrate
  python manage.py createsuperuser 
  # Add a backup code to "username" to login with otp
  python manage.py addstatictoken username
  # Run server
  python manage.py runserver
  ``` 

- HTTPS (Optional)
  - Install and setup caddy with Caddyfile in the project root for https and other functionalities. (Or use your own reverse proxy)
  - Uncomment last 5 lines of settings.py
  - Note that enabling HTTPS doesn't make your site secure, there is also disabling https, change secret key, etc. (Not to mention my code might have exploit). See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/


## Coding details
Web terminal is implemented with websocket, frontend is xterm.js. Backend is implemented with pty.fork()
pseudo terminal. User login with "su --loign"

File manager operations are done with websocket. File upload using ajax and http. File download with http.

Modified django-otp to separate login and otp page and added support for authentication with websocket.