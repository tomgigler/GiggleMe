# GiggleMe

GiggleMe is a Discord bot for scheduling messages. Over time it has also grown support for repeating messages, templates, proposals and voting, automatic replies, time-zone handling, VIP/voice-channel behavior, and other server-specific features.

The bot is primarily written in Python and stores persistent state in MySQL. The repository also contains an optional PHP-based web interface that uses the same database.

> **Project status**
>
> GiggleMe grew organically around real users and their feature requests. Some parts of the implementation are more general than others, and some behaviors are intentionally specialized. Refactoring is ongoing, so preserving existing behavior is preferred over silently changing unusual logic.

## Requirements

A basic bot deployment requires:

- Python 3 (the current known-working deployment uses Python 3.6.9)
- MySQL or a compatible MySQL server
- a Discord application/bot
- the Python packages listed in `requirements.txt`
- a local `settings.py` containing deployment-specific settings and secrets

For the optional web interface you will also need a PHP-capable web server with access to the same MySQL database.

## 1. Clone the repository

```bash
git clone https://github.com/tomgigler/GiggleMe.git
cd GiggleMe
```

## 2. Create the MySQL database

The repository includes `schema.sql`, which creates the `giggleme` database, creates the tables used by the application, and installs the required timezone seed data.

From a shell:

```bash
mysql -u root -p < schema.sql
```

Or from inside the MySQL client:

```sql
SOURCE /path/to/GiggleMe/schema.sql;
```

The schema contains these tables:

- `channels`
- `guilds`
- `messages`
- `mute_members`
- `request_queue`
- `timezones`
- `user_guilds`
- `users`
- `vips`
- `votes`

The supplied schema intentionally mirrors the existing production schema. It does not add foreign keys, new indexes, or charset changes that are not already present in the running application.

### Create a dedicated MySQL user

Using a dedicated account is recommended instead of running GiggleMe as MySQL `root`.

Example:

```sql
CREATE USER 'giggleme'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON giggleme.* TO 'giggleme'@'localhost';
FLUSH PRIVILEGES;
```

Adjust the MySQL host and permissions to match your deployment.

## 3. Create the Discord bot

Create a Discord application and bot for your deployment, then invite that bot to the servers where you want to use GiggleMe.

The current code creates the Discord client using all Discord intents. A self-hosted deployment must therefore enable the intents required by the current application in the Discord developer configuration.

Reducing GiggleMe to the minimum required intent set is a planned cleanup and is preferable to requesting every intent indefinitely.

Keep the bot token private. Do not commit it to Git.

## 4. Create `settings.py`

GiggleMe reads deployment-specific configuration from a local Python module named:

```text
settings.py
```

A safe template is included in the repository as:

```text
settings.example.py
```

Copy it:

```bash
cp settings.example.py settings.py
```

Then edit `settings.py` and supply values for:

```python
bot_token = "YOUR_DISCORD_BOT_TOKEN"
bot_owner_id = 123456789012345678

db_user = "giggleme"
db_password = "YOUR_MYSQL_PASSWORD"
database = "giggleme"

twitter_consumer_key = "YOUR_TWITTER_CONSUMER_KEY"
twitter_consumer_secret = "YOUR_TWITTER_CONSUMER_SECRET"
```

### Setting meanings

- `bot_token` - Discord bot token for this GiggleMe instance.
- `bot_owner_id` - Discord user ID of the bot owner.
- `db_user` - MySQL account used by GiggleMe.
- `db_password` - password for that MySQL account.
- `database` - MySQL database name. The supplied `schema.sql` creates `giggleme`.
- `twitter_consumer_key` - consumer/API key used by the Twitter/X-related integration.
- `twitter_consumer_secret` - corresponding consumer/API secret.

Keep `settings.py` private. Do not commit production credentials.

Before committing anything, verify that Git ignores the real file:

```bash
git check-ignore settings.py
```

If that command does not print `settings.py`, add this to `.gitignore`:

```gitignore
settings.py
```

If a real `settings.py` containing credentials was ever committed to a public repository, deleting it from a later commit does not make those credentials private again. Rotate them.

## 5. Install Python dependencies

The current production installation is known to work with:

```text
Python 3.6.9
discord.py 1.7.3
mysql-connector-python 8.0.22
python-dateutil 2.8.1
pytz 2020.1
python-twitter 3.5
```

Those exact direct dependencies are pinned in `requirements.txt` so a new deployment can reproduce the known-working environment before attempting any Python or library upgrades.

### Existing production-style installation

The original GiggleMe server runs the system Python directly rather than using a virtual environment. To reproduce that arrangement, install the dependencies for the same `python3` interpreter that will run the bot:

```bash
python3 -m pip install -r requirements.txt
```

Confirm the interpreter path:

```bash
command -v python3
```

On the original deployment this is:

```text
/usr/bin/python3
```

### Optional virtual environment

A fresh installation may instead use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

If you do this, the systemd `ExecStart=` line must point to `venv/bin/python` instead of `/usr/bin/python3`.

Python 3.6.9 and the pinned package versions are the **known-working baseline**, not a recommendation that new development remain on them forever. Runtime and library modernization should be handled separately and tested as an intentional refactor.

## 6. Start the bot manually

`gigglebot.py` imports modules stored in both the repository root and `util/`, so both locations must be on Python's module search path.

From the repository root, using the system Python as the original deployment does:

```bash
export PYTHONPATH="$PWD:$PWD/util${PYTHONPATH:+:$PYTHONPATH}"
python3 gigglebot.py
```

If you installed the dependencies into a virtual environment, activate it first and run `python gigglebot.py` instead.

The repository also contains `restart-giggleme.sh`, which reflects the original production deployment. It sets `PYTHONPATH`, stops an existing `gigglebot.py` process, and starts a new one in the background with `python3`.

That script remains useful for simple/manual deployments, but a service manager is strongly recommended for a permanent installation so the bot restarts automatically after a crash or server reboot.

## 7. Run GiggleMe with systemd (recommended)

An example systemd unit is provided at:

```text
deploy/giggleme.service.example
```

The supplied example uses `/usr/bin/python3`, matching the original production deployment. It does **not** assume that a `venv` directory exists.

First confirm the path to the Python interpreter that already runs GiggleMe successfully:

```bash
command -v python3
```

Copy the example unit to the systemd service directory and edit it:

```bash
sudo cp deploy/giggleme.service.example /etc/systemd/system/giggleme.service
sudo nano /etc/systemd/system/giggleme.service
```

Before enabling it, edit these values:

- `User=` - Linux account that owns/runs the GiggleMe installation.
- `WorkingDirectory=` - absolute path to the cloned GiggleMe repository.
- `Environment=PYTHONPATH=...` - the same absolute repository path plus its `util/` directory.
- `ExecStart=` - absolute path to the Python executable that has GiggleMe's dependencies installed, followed by the absolute path to `gigglebot.py`.

For a system-Python installation at `/home/tom/GiggleMe`:

```ini
User=tom
WorkingDirectory=/home/tom/GiggleMe
Environment="PYTHONPATH=/home/tom/GiggleMe:/home/tom/GiggleMe/util"
ExecStart=/usr/bin/python3 /home/tom/GiggleMe/gigglebot.py
```

For an installation using `/home/tom/GiggleMe/venv`, only the executable changes:

```ini
ExecStart=/home/tom/GiggleMe/venv/bin/python /home/tom/GiggleMe/gigglebot.py
```

Do not use the virtual-environment form unless that file actually exists. You can verify an executable before enabling the service:

```bash
ls -l /usr/bin/python3
# or, if using a virtual environment:
ls -l /home/tom/GiggleMe/venv/bin/python
```

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now giggleme
```

Check status:

```bash
systemctl status giggleme
```

Restart it deliberately:

```bash
sudo systemctl restart giggleme
```

Stop it:

```bash
sudo systemctl stop giggleme
```

Follow its logs:

```bash
journalctl -u giggleme -f
```

Or inspect recent logs:

```bash
journalctl -u giggleme --since "1 hour ago"
```

The supplied unit uses `Restart=on-failure` with a ten-second delay. If `gigglebot.py` exits unexpectedly, systemd starts it again. An intentional `systemctl stop giggleme` remains stopped.

A systemd exit status of `203/EXEC` normally means the executable in `ExecStart=` could not be launched. Check that the Python path exists and is executable before chasing application-level problems.

Once the systemd deployment has been tested, `restart-giggleme.sh` can optionally be simplified to call `systemctl restart giggleme` instead of locating and killing the Python process itself.

## 8. Verify the bot

Once connected to Discord, use:

```text
~giggle help
```

to display GiggleMe's built-in command help.

A useful initial smoke test is:

1. Confirm the bot comes online.
2. Run `~giggle help`.
3. Set or verify your timezone.
4. Schedule a test message a few minutes in the future.
5. Restart GiggleMe.
6. Confirm the scheduled message is reloaded from MySQL and delivered at the expected time.

If using systemd, also test automatic recovery once during initial deployment by restarting the service and confirming it returns cleanly.

## Optional web interface

The repository contains a PHP-based web interface under `web/`. It is not required to run the Discord bot, but it provides another way to work with GiggleMe data and scheduled messages.

The web interface and bot use the same MySQL database. The web side can write requests to `request_queue`, which the running bot polls so that changes made through the website can be reflected in the bot's in-memory state.

### Web hosting requirements

At minimum, a web deployment needs:

- a web server capable of running PHP
- PHP with MySQL connectivity
- network/database access to the same MySQL database used by the bot
- a private configuration containing the database credentials required by the PHP code
- HTTPS for any deployment exposed beyond a trusted local network

The simplest layout is to expose the contents of `web/` from a PHP-enabled virtual host or subdirectory. Do **not** expose the repository root as the web document root; files such as `settings.py` contain secrets and must never be web-accessible.

For example, the public document root should point at something equivalent to:

```text
/path/to/GiggleMe/web
```

not:

```text
/path/to/GiggleMe
```

### Web configuration status

The bot-side deployment configuration is now documented through `settings.example.py`, but the web side does not yet have a sanitized, documented configuration template in this deployment bundle.

Before considering the web deployment documentation complete, the files under `web/` should be traced for:

- MySQL host/user/password/database settings
- Discord/OAuth or other authentication settings, if any
- callback/base URLs
- writable directories, if any
- required PHP extensions
- web-server rewrite rules, if any

Those values should then be moved into or represented by a committed example configuration while the real configuration remains ignored by Git.

Until that is done, treat the web interface as optional and review its local configuration before exposing it publicly. The bot itself can be deployed without it.

## How scheduling is stored

The `messages` table is shared by several message-like features.

The current application distinguishes message types partly through `delivery_time`:

- `delivery_time >= 0`: scheduled message
- `delivery_time = -1`: proposal
- `delivery_time = -2`: auto-reply
- other/null cases: template behavior

This is existing application behavior and should not be changed casually because existing database rows depend on it.

Scheduled messages can also contain repeat information, a repeat-until time, and `special_handling` flags used by particular delivery behaviors.

## Database notes

The production-derived schema contains ten tables and no MySQL triggers or scheduled MySQL events.

Several relationships are maintained by application logic rather than MySQL foreign-key constraints. Guild, user, channel, template, and proposal IDs are related across tables without declared foreign keys.

The schema also contains a historical mixture of `utf8mb4` and `latin1` tables. `schema.sql` preserves that behavior intentionally. Charset normalization should be performed as a deliberate migration, not folded into initial installation.

The `timezones` table is seeded with stable numeric IDs:

| ID | Name |
|---:|---|
| 1 | UTC |
| 2 | US/Pacific |
| 3 | US/Eastern |
| 4 | US/Central |
| 5 | US/Mountain |

Those IDs are persisted in user records and should not be renumbered without a migration.

## Security

Do not commit or expose:

- Discord bot tokens
- MySQL passwords
- Twitter/X API secrets
- production `settings.py`
- private web configuration

Use a dedicated MySQL account for GiggleMe and grant only the access required by the application.

Do not configure a web server with the GiggleMe repository root as its public document root. Only the intended contents of `web/` should be exposed.

For a long-running Linux deployment, run GiggleMe as an ordinary unprivileged Linux account rather than `root` when practical.

## Project layout

```text
GiggleMe/
├── gigglebot.py                  # main Discord bot
├── util/                         # database, parsing, models, timezone and helper modules
├── web/                          # optional PHP/JavaScript web interface
├── deploy/
│   └── giggleme.service.example # example systemd unit
├── restart-giggleme.sh           # original restart helper
├── schema.sql                    # MySQL schema and required seed data
├── settings.example.py           # safe template for local deployment settings
├── requirements.txt              # known-working Python dependency versions
├── README.md
└── LICENSE
```

## Development notes

GiggleMe has accumulated features incrementally over a long period of real-world use. Before removing or simplifying strange-looking behavior, trace where it is used. A branch that appears redundant may exist because one server or user requested a specific behavior.

Useful refactoring/deployment goals include:

- replace `discord.Intents.all()` with the minimum required intents
- document and sanitize the web interface configuration
- split the large `on_message` command dispatcher into focused command handlers
- add database migrations for future schema changes
- normalize magic values and flags into named types/constants
- modernize Python and third-party dependencies in a controlled upgrade
- add automated tests around scheduling and persistence before large structural changes

## License

GiggleMe is released under the MIT License.
