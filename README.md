# Kingshot Gift Code Bot

Automated bot for redeeming gift codes in Kingshot game. Automatically fetches active codes from [kingshot.net](https://kingshot.net/gift-codes) and redeems them for your account.

## Requirements

- Python 3.x
- Google Chrome browser
- ChromeDriver (matching your Chrome version)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `login_id.txt` file with your Player ID:
```
YOUR_ACCOUNT_ID
```

## Usage

### Headless mode (invisible browser)
```bash
python bot.py
```

### Visible mode (see the browser)
```bash
python bot.py --visible
```

## How it works

1. Fetches active gift codes from kingshot.net
2. Opens the official redemption page
3. Logs in with your Player ID
4. Redeems each active code automatically
5. Generates a log file with results

## Output

- Console output shows progress in real-time
- Log file `bot_log_YYYYMMDD_HHMMSS.txt` is created with full details
- Summary shows successful/failed redemptions

## Files

- `bot.py` - Main bot script
- `login_id.txt` - Your Player ID (create this file)
- `requirements.txt` - Python dependencies
- `bot_log_*.txt` - Generated log files

## Notes

- Codes are fetched automatically from kingshot.net
- Only active (non-expired) codes are redeemed
- 3-second delay between each code to avoid rate limiting
- ChromeDriver must be installed and in PATH

## Disclaimer

This bot is for personal use only. Use at your own risk.
