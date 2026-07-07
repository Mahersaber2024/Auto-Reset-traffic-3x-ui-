# Auto-Reset-Traffic for 3x-UI

A lightweight and efficient tool for automatically resetting traffic for **specific users** on your [3x-UI](https://github.com/MHSanaei/3x-ui) panel.

## Overview

Auto-Reset-Traffic for 3x-UI is a Python-based utility designed for server owners who want to reset traffic usage for selected clients on a schedule.
Unlike global reset scripts, this project focuses only on the users you define in the configuration file, making it safer and more flexible for subscription-based VPN services.

> This tool works alongside the [3x-UI panel](https://github.com/MHSanaei/3x-ui) and does not modify or replace it — it only connects to it to reset traffic for the users you choose.

## Features

- Automatically resets traffic **only for selected users**, not all clients.
- Scheduled execution using a **systemd timer**.
- Supports daily, hourly, or custom intervals.
- Interactive management menu with `x3-tf`.
- Full logging support for troubleshooting and monitoring.
- Simple one-command installation and uninstallation.
- Lightweight Python implementation.

## Requirements

- Linux server with `systemd`.
- Python 3.
- 3x-UI panel access (IP/domain, port, path, username, password).
- Root or sudo privileges.

## Installation

Run the installer with:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-/main/install.sh)
```

During installation you'll be asked for your 3x-UI panel details (address, port, web base path, username, and password). These are used only to connect to your own panel.

## Usage

Once installed, the service runs automatically through the systemd timer. To manage everything, just run:

```bash
x3-tf
```

This opens an interactive menu where you can:

- Add/remove users from the auto-reset list
- Change the reset interval (hourly, daily, custom)
- Run a manual reset
- View logs

## How It Works

1. The script reads the list of users from `config.conf`.
2. It connects to your 3x-UI panel.
3. It resets traffic only for the selected users.
4. The process runs on schedule through the systemd timer.

## Logging

All operations are logged so you can review execution results and troubleshoot problems easily.

```bash
journalctl -u x3-tf.service -f
```

## Uninstallation

To remove the project completely, run:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-/main/uninstall.sh)
```

## Notes

- This tool does **not** reset traffic for all users by default — only the ones listed in `config.conf`.
- Make sure the emails in `config.conf` are correct before enabling the timer.
- Always test on a small set of users first.

## Contributing

Pull requests and improvements are welcome. Fork the repository, create a branch, and submit a pull request.

## License

MIT

## Disclaimer

Use this tool responsibly and only on servers and accounts you manage.
