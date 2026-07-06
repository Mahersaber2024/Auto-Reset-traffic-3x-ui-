# Auto-Reset-Traffic for 3x-UI

A lightweight and efficient tool for automatically resetting traffic for **specific users** on your 3x-UI panel.

## Overview

Auto-Reset-Traffic for 3x-UI is a Python-based utility designed for server owners who want to reset traffic usage for selected clients on a schedule.  
Unlike global reset scripts, this project focuses only on the user IDs you define in the configuration file, making it safer and more flexible for subscription-based VPN services.

## Features

- Automatically resets traffic **only for selected users**, not all clients.
- Scheduled execution using **systemd timer**.
- Supports daily, hourly, or custom intervals.
- Interactive management menu with `x3-tf`.
- Full logging support for troubleshooting and monitoring.
- Simple one-command installation and uninstallation.
- Lightweight Python implementation.
- Designed for easy integration with 3x-UI based setups.

## Project Structure

- `install.sh` — Installation script.
- `manager.py` — Interactive management menu.
- `reset_daemon.py` — Main traffic reset daemon.
- `config.conf` — List of user IDs to reset.
- `requirements.txt` — Python dependencies.
- `x3-tf.service` — systemd service file.
- `x3-tf.timer` — systemd timer file.
- `uninstall.sh` — Uninstallation script.

## Requirements

- Linux server with `systemd`.
- Python 3.
- 3x-UI panel access.
- `curl` and `bash` for installation.
- Root or sudo privileges.

## Installation

Run the installer with:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-/main/install.sh)
```

## Configuration

After installation, edit the configuration file and add the user IDs you want to reset.

Example:

```conf
1
5
12
24
```

Each line should contain one user ID.

## Usage

After installation, the service can run automatically through systemd timer.

Common management command:

```bash
x3-tf
```

This menu can be used to manage the service, timer, logs, and configuration.

### Manual run

If you want to test the reset daemon manually:

```bash
python3 reset_daemon.py
```

## How It Works

1. The script reads the user IDs from `config.conf`.
2. It connects to your 3x-UI environment.
3. It resets traffic only for the selected users.
4. The process runs on schedule through `systemd timer`.

## Logging

All operations are logged so you can review execution results and troubleshoot problems easily.  
If something does not work as expected, check the service logs first.

Example:

```bash
journalctl -u x3-tf.service -f
```

## Uninstallation

To remove the project completely, run:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-/main/uninstall.sh)
```

## Notes

- This tool does **not** reset traffic for all users by default.
- Make sure the user IDs in `config.conf` are correct before enabling the timer.
- Always test on a small set of users first.

## Contributing

Pull requests and improvements are welcome.  
If you want to contribute, fork the repository, create a branch, and submit a pull request.

## License

Add your preferred license here, for example MIT.

## Disclaimer

Use this tool responsibly and only on servers and accounts you manage.
