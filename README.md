# 🔔 Taionca Discord Notificator

Automated Discord notification system to monitor employee attendance, old work orders (ODTs), debts, and low stock in the Taionca database.

## 📋 Description

This Discord bot connects to a PostgreSQL database and sends automatic notifications about:

- **📆 Employee Attendance**: Notifies if an employee hasn't recorded attendance in the last 2 days
- **📜 Old ODTs**: Alerts about work orders (ODTs) open for more than 2 months
- **💰 Debts**: Reports on pending employee loans
- **📋 Low Stock**: Notifies when products have stock below the average level

Notifications are sent on specific days of the month (12, 14, 27, and second-to-last day) for biweekly reviews.

## 🔧 Prerequisites

- Python 3.7 or higher
- PostgreSQL (remote database already configured)
- Discord account with a configured bot

## 📦 Installation

### 1. Clone or download the project

**Windows (PowerShell):**
```powershell
cd c:\Proyectos
git clone https://github.com/Bruchogun/Taionca-discord-notificator.git
cd Taionca-discord-notificator
```

**Linux/Mac (Bash):**
```bash
cd ~/projects
git clone https://github.com/Bruchogun/Taionca-discord-notificator.git
cd Taionca-discord-notificator
```

### 2. Create a virtual environment

**Windows (PowerShell):**
```powershell
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

> **Note**: If you encounter a permissions error, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Linux/Mac (Bash):**
```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### 3. Install dependencies

With the virtual environment activated:

**Windows (PowerShell):**
```powershell
pip install -r requirements.txt
```

**Linux/Mac (Bash):**
```bash
pip install -r requirements.txt
```

Or install manually:

**Windows (PowerShell):**
```powershell
pip install psycopg2-binary discord.py pytz python-dotenv
```

**Linux/Mac (Bash):**
```bash
pip install psycopg2-binary discord.py pytz python-dotenv
```

#### Project dependencies:

- **psycopg2-binary** (2.9+): PostgreSQL connector for Python
- **discord.py** (2.0+): Library to interact with the Discord API
- **pytz**: Timezone handling
- **python-dotenv**: Load environment variables from .env file

### 4. Configure environment variables

Copy the example environment file and edit it with your credentials:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```

**Linux/Mac (Bash):**
```bash
cp .env.example .env
nano .env  # or use vim, gedit, etc.
```

Edit the `.env` file with your actual values:

```env
# Database Configuration
DB_HOST=35.230.112.171
DB_NAME=dev
DB_USER=dev
DB_PASSWORD=your_database_password
DB_PORT=5433

# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_USER_ID=your_discord_user_id

# Monitoring Configuration
USERS_TO_MONITOR=4,11,22
```

**Important:** Never commit the `.env` file to version control. It's already included in `.gitignore`.

### 5. Verify installation

**Windows (PowerShell):**
```powershell
pip list
```

**Linux/Mac (Bash):**
```bash
pip list
```

You should see the installed libraries with their versions.

## ⚙️ Configuration

### 1. Configure the Discord Bot

If you need to create a new Discord bot:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. In the "Bot" section, create a bot and copy the **Token**
4. Enable **Message Content Intent** in Bot Settings
5. Invite the bot to your server with "Send Messages" permissions
6. Add the token to your `.env` file in the `DISCORD_BOT_TOKEN` variable

### 2. Configure IDs

**To get your Discord ID:**
1. Enable Developer Mode in Discord (User Settings > Advanced)
2. Right-click on your username > Copy ID
3. Add it to your `.env` file in the `DISCORD_USER_ID` variable

**To configure users to monitor:**
- Edit the `USERS_TO_MONITOR` variable in `.env` with comma-separated user IDs from your database
- Example: `USERS_TO_MONITOR=4,11,22`

### 3. Database Configuration

All database credentials are now stored in the `.env` file. Update them as needed:

```env
DB_HOST=35.230.112.171
DB_NAME=dev
DB_USER=dev
DB_PASSWORD=your_actual_password
DB_PORT=5433
```

> ⚠️ **Security**: The `.env` file contains sensitive information and should never be committed to version control. It's already included in `.gitignore`.

## 🚀 Usage

### Manual Execution

With the virtual environment activated:

**Windows (PowerShell):**
```powershell
python notifications.py
```

**Linux/Mac (Bash):**
```bash
python3 notifications.py
```

The bot will run and:
1. Connect to the PostgreSQL database
2. Start the Discord bot
3. Check attendance for specified users
4. If it's a review day (12, 14, 27, or second-to-last of the month), it will also check:
   - Debts
   - Old ODTs
   - Low stock
5. Send notifications via Discord direct message
6. Close automatically

### Automation

#### Windows (Task Scheduler)

To run the bot automatically every day:

1. Open Windows **Task Scheduler**
2. Create a new basic task
3. Configure the trigger to run daily
4. In the action, select "Start a program"
5. Program:
   ```
   C:\Proyectos\Taionca-discord-notificator\venv\Scripts\python.exe
   ```
6. Arguments:
   ```
   notifications.py
   ```
7. Start in:
   ```
   C:\Proyectos\Taionca-discord-notificator
   ```

#### Linux/Mac (Cron)

To run the bot automatically every day using cron:

1. Open the crontab editor:
   ```bash
   crontab -e
   ```

2. Add a line to run the script daily (example: every day at 9:00 AM):
   ```bash
   0 9 * * * cd ~/projects/Taionca-discord-notificator && ./venv/bin/python3 notifications.py >> ~/projects/Taionca-discord-notificator/logs.txt 2>&1
   ```

3. Save and exit. The cron job is now active.

**Cron schedule examples:**
- `0 9 * * *` - Every day at 9:00 AM
- `0 */6 * * *` - Every 6 hours
- `30 8 * * 1-5` - Every weekday at 8:30 AM

**Note:** Make sure to use absolute paths in your cron job.

## 📊 Detailed Functionality

### Attendance Check
- Runs every day
- Checks if specified users haven't recorded attendance in 2+ days
- Shows the date of the last record in Spanish

### ODT Check
- Only runs on specific days (12, 14, 27, second-to-last)
- Searches for open ODTs older than 2 months
- Shows: ID, responsible person, amount, client, opening date, and description

### Debt Check
- Only runs on specific days
- Lists all pending loans (amount != 0)
- Sorted by amount from highest to lowest

### Stock Check
- Only runs on specific days
- Identifies products with current stock below average stock
- Calculates the necessary replenishment cost
- Sorted by replenishment cost (priority)

## 🛠️ Troubleshooting

### PostgreSQL connection error
- Verify you have an internet connection
- Confirm the server IP is accessible
- Verify database credentials in your `.env` file

### Spanish locale error
- The code has automatic fallback if Spanish locale is not found
- On Windows, it should use `Spanish_Spain.1252`
- If there are issues, it will install the default locale and use hardcoded month names

### Bot doesn't send messages
- Verify the bot token in `.env` is correct
- Confirm your Discord ID in `.env` is correct
- Make sure you accept DMs from the bot (you haven't blocked it)
- Verify the bot has the correct permissions

### Virtual environment won't activate

**Windows:**
- Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Then try activating again: `.\venv\Scripts\Activate.ps1`

**Linux/Mac:**
- Make sure you have execute permissions: `chmod +x venv/bin/activate`
- Then activate: `source venv/bin/activate`

### Missing .env file error
- Make sure you copied `.env.example` to `.env`
- Verify all required variables are filled in `.env`

## 📝 Logs and Debugging

The script prints useful information to the console:
- PostgreSQL connection status
- Discord bot connection status
- Number of notifications prepared
- Message sending confirmation

To save logs to a file:

**Windows (PowerShell):**
```powershell
python notifications.py > logs.txt 2>&1
```

**Linux/Mac (Bash):**
```bash
python3 notifications.py > logs.txt 2>&1
```

## 🔒 Security

**Security improvements implemented:**

1. **Environment Variables**: All sensitive credentials (database passwords, Discord tokens, user IDs) are now stored in the `.env` file instead of being hardcoded
2. **Git Protection**: The `.env` file is excluded from version control via `.gitignore`
3. **Example File**: `.env.example` provides a template without exposing real credentials

**Best practices:**
- Never commit the `.env` file to version control
- Never share your `.env` file or its contents
- Use different credentials for development and production
- Rotate tokens and passwords regularly
- For production, consider using:
  - Azure Key Vault
  - AWS Secrets Manager
  - Other enterprise secrets management solutions

## 📄 Project Structure

```
Taionca-discord-notificator/
│
├── venv/                      # Virtual environment (not included in git)
├── notifications.py           # Main script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not included in git)
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore file
├── README.md                  # This file
└── logs.txt                  # Log file (optional)
```

## 🤝 Contributions

To contribute to the project:
1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📧 Contact

For questions or support, contact the Taionca development team.

---

**Last updated**: November 2025
