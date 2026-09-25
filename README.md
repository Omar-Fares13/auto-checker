# Zoho People Attendance Automation

Automates Zoho People **check-in and check-out** on weekdays using GitHub Actions, with Telegram notifications for success or failure.

## Requirements

* Zoho People account
* GitHub repository
* Telegram account

## Zoho Security Configuration

The current web-login implementation requires **MFA and Additional Verification to be disabled**.

### Disable MFA

1. Go to `accounts.zoho.com`.
2. Open **Multi-factor Authentication** from the left menu.
3. Go to **MFA modes**.
4. Turn off the toggle.

### Disable Additional Verification

> This option is available only for personal accounts. Organization accounts may not have the option to disable it.

1. Go to `accounts.zoho.com`.
2. Open **Security** and select **Password**.
3. Find **Additional Verification**.
4. Turn off the toggle.

<img width="1711" height="289" alt="Additional Verification" src="https://github.com/user-attachments/assets/f3bd411e-ccd6-478b-ad09-c9ee2575bc40" />


> Disabling these security features reduces account security. Re-enable them when the automation is no longer required.

## GitHub Secrets

Go to:

**Repository → Settings → Secrets and variables → Actions → New repository secret**

Add:

| Secret               | Value                 |
| -------------------- | --------------------- |
| `ZOHO_EMAIL`         | Zoho account email    |
| `ZOHO_PASSWORD`      | Zoho account password |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token    |
| `TELEGRAM_CHAT_ID`   | Telegram chat ID      |

## Telegram Setup

1. Open Telegram and message **@BotFather**.
2. Run `/newbot` and follow the instructions.
3. Add the generated token as `TELEGRAM_BOT_TOKEN`.
4. Send any message to your new bot.
5. Open `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`.
6. Find your chat ID and add it as `TELEGRAM_CHAT_ID`.

## Schedule

* **Check-in:** 10:00 AM
* **Check-out:** 6:00 PM
* **Sunday–Thursday**
* **Africa/Cairo timezone**

Both workflows can also be triggered manually from the **Actions** tab.

## Files

```text
.
├── checkin.py
├── checkout.py
└── .github/
    └── workflows/
        ├── checkin.yml
        └── checkout.yml
```

## Security Note

Never commit credentials, `.env` files, session cookies, or tokens to the repository. Use **GitHub Secrets** for sensitive values.

This automation is intended for authorized use on your own Zoho People account.
