# ujn-library-assassin

A auto seat booking program mainly designed for students in UJN.

## Installation

1. copy `.env.sample` to `.env`, add captcha service 
2. copy `users.sample.json` to `users.json` (If using CLI)
3. `pip3 install -r requirements.txt`

## Usage-CLI

The CLI version is mainly targeted at students in University of Jinan, e.g. the seat is available for booking on the previous day at 7:00 a.m., and the seat is unavailable during 12:00 a.m. to 4:00 p.m. every tuesday for maintenance.

> If you're students from other school and your school has different policies, please edit the `cli.py` manually, and the CLI version won't receive new features in the future.

1. Edit `users.json`
2. Execute `cli.py` every day for booking

### Persistance with systemd

1. Edit `/etc/systemd/system/ujnlib.service`

```
[Unit]
Description=UJN library auto booking

[Service]
Type=oneshot
WorkingDirectory=/opt/ujn-library-assassin
ExecStart=/usr/bin/env python3 cli.py
Environment="TZ=Asia/Shanghai"
```

2. Edit `/etc/systemd/system/ujnlib.timer`

```
[Unit]
Description=Run seat booking everyday at 6:59

[Timer]
OnCalendar=06:59 Asia/Shanghai
Persistent=true

[Install]
WantedBy=timers.target
```

3. `systemctl daemon-reload`
4. `systemctl enable --now ujnlib.timer`

## Usage-Server

Not implemented yet.

## LICENSE

```
ujn-library-assassin
Copyright (C) 2022, SpartaEN <i@evo.moe> 

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```