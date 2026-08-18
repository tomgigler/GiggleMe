# GiggleMe

GiggleMe is a Discord bot for scheduling messages. Over time it has also grown support for repeating messages, templates, automatic replies, time-zone handling, VIP/voice-channel behavior, and other server-specific features.

The bot is primarily written in Python and stores persistent state in MySQL. The repository also contains an optional PHP-based web interface that uses the same database.

> **Project status**
>
> GiggleMe grew organically around real users and their feature requests. Some parts of the implementation are more general than others, and some behaviors are intentionally specialized. Refactoring is ongoing, so preserving existing behavior is preferred over silently changing unusual logic.

## Requirements

A basic bot deployment requires:

- Python 3.6.9 is the current known-working runtime; other Python versions have not yet been verified with the pinned legacy dependencies
- MySQL or a compatible MySQL server running on the same host as the bot
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

The supplied schema is the current GiggleMe baseline. Existing installations may require deliberate database migrations before their tables match it.

### Create a dedicated MySQL user

Using a dedicated account is recommended instead of running GiggleMe as MySQL `root`.

The current bot database layer connects to `localhost` directly; there is no `db_host` setting yet. A standard self-hosted deployment should therefore run MySQL on the same machine as the bot unless the database layer is changed.

The bot's normal runtime database operations are reads and row-level inserts/updates/deletes, so the application account does not need broad administrative privileges:

```sql
CREATE USER 'giggleme'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON giggleme.* TO 'giggleme'@'localhost';
FLUSH PRIVILEGES;
```

Use an administrative MySQL account only for initial schema creation or future schema migrations.

## 3. Create the Discord bot

Create a Discord application and bot for your deployment, then invite that bot to the servers where you want to use GiggleMe.

The current code creates the Discord client using `discord.Intents.all()`. It also reads normal message content and handles voice-state events, so Discord gateway intent configuration is a real runtime requirement rather than optional decoration.

The exact minimum intent set has not yet been documented. Until that cleanup is completed, a self-hosted deployment should preserve the intent configuration expected by the current bot/library combination rather than disabling intents experimentally.

Reducing GiggleMe to the minimum required intent set is a planned cleanup and should be handled as a tested code change, not merely a documentation edit.

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

There is currently no `db_host` setting. The Python database layer connects to MySQL on `localhost`.
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

### Use a virtual environment

A Python virtual environment is recommended for GiggleMe so its dependencies are isolated from the system Python and from other applications on the server.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The virtual environment is local deployment state and should not be committed. The repository `.gitignore` excludes:

```gitignore
.venv/
```

After activation, `python` and `pip` refer to the executables inside `.venv`.

The original production deployment used the system Python directly. That remains a useful historical reference, but new installations should prefer the virtual-environment setup above.

Python 3.6.9 and the pinned package versions are the **known-working baseline**, not a recommendation that new development remain on them forever. Runtime and library modernization should be handled separately and tested as an intentional refactor.

## 6. Start the bot manually

`gigglebot.py` imports modules stored in both the repository root and `util/`, so both locations must be on Python's module search path.

From the repository root:

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD:$PWD/util${PYTHONPATH:+:$PYTHONPATH}"
python gigglebot.py
```

You can also run the virtual environment's interpreter directly without activating it:

```bash
export PYTHONPATH="$PWD:$PWD/util${PYTHONPATH:+:$PYTHONPATH}"
.venv/bin/python gigglebot.py
```

The repository also contains `restart-giggleme.sh`, which reflects the original production deployment and uses the system `python3`. For a virtual-environment installation, prefer the commands above or systemd rather than the legacy restart script.

Once GiggleMe is managed by systemd, use `systemctl restart giggleme` for restarts. Mixing the legacy script with systemd can leave the running bot outside systemd's control.

## 7. Run GiggleMe with systemd (recommended)

An example systemd unit is provided at:

```text
deploy/giggleme.service.example
```

The supplied example assumes GiggleMe's virtual environment is located at `.venv/` inside the repository. systemd does not need to activate the environment; it executes `.venv/bin/python` directly.

Copy the example unit to the systemd service directory and edit it:

```bash
sudo cp deploy/giggleme.service.example /etc/systemd/system/giggleme.service
sudo nano /etc/systemd/system/giggleme.service
```

Before enabling it, edit these values:

- `User=` - Linux account that owns/runs the GiggleMe installation.
- `WorkingDirectory=` - absolute path to the cloned GiggleMe repository.
- `Environment=PYTHONPATH=...` - the same absolute repository path plus its `util/` directory.
- `ExecStart=` - absolute path to `.venv/bin/python`, followed by the absolute path to `gigglebot.py`.

For an installation at `/home/tom/GiggleMe`:

```ini
User=tom
WorkingDirectory=/home/tom/GiggleMe
Environment="PYTHONPATH=/home/tom/GiggleMe:/home/tom/GiggleMe/util"
ExecStart=/home/tom/GiggleMe/.venv/bin/python /home/tom/GiggleMe/gigglebot.py
```

Verify the virtual-environment interpreter exists before enabling the service:

```bash
ls -l /home/tom/GiggleMe/.venv/bin/python
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

Once the systemd deployment has been tested, use `systemctl` for starts, stops, and restarts. Do not continue using the original `restart-giggleme.sh` against a systemd-managed installation.

If desired, `restart-giggleme.sh` can later be simplified into a wrapper around `systemctl restart giggleme`.

## 8. Verify the bot

GiggleMe's primary command interface is Discord slash commands. Start with:

```text
/giggle help
```

Classic time-based scheduling syntax is no longer executable. If a user enters an old command such as `~giggle 5`, GiggleMe recognizes the scheduling pattern only to direct the user to `/giggle schedule` help.

Auto Reply configuration uses `/giggle auto-reply create`. Auto Reply matching still requires the privileged Message Content intent because triggering messages are ordinary server messages. Classic `~giggle help` remains temporarily as migration guidance.

A useful smoke test is:

1. Confirm the bot comes online and `/giggle` appears in the command picker.
2. Run `/giggle help` and confirm the expected command groups are present.
3. Set or verify your timezone and time format.
4. Create a template, then schedule a message from it a few minutes in the future.
5. List, show, edit, and cancel stored messages, including channel autocomplete where applicable.
6. Exercise send/cancel confirmation buttons.
7. Grant and revoke a user's GiggleMe authorization and confirm the `user_guilds` row changes as expected.
8. Create an Auto Reply with `/giggle auto-reply create`, trigger it from an ordinary server message, then list/show/cancel it.
9. List, add, and remove a VIP.
10. Enter an old classic scheduling command and confirm it returns slash scheduling help without creating a message.
11. Restart GiggleMe and confirm the full `/giggle` command tree is still registered.
12. Confirm a scheduled message survives the restart and is delivered at the expected time.

The command tree is synchronized for existing guilds during `on_ready()` and for newly joined guilds during `on_guild_join()`.

If using systemd, also test automatic recovery once during initial deployment by restarting the service and confirming it returns cleanly.

## 9. Optional: host the web interface

GiggleMe also includes a PHP/JavaScript web interface under `web/`. The bot does not require the website, but the website uses the same MySQL database and can make changes that the running bot notices through the `request_queue` table.

### Important: expose only `web/`

The web server's public document root should be:

```text
/path/to/GiggleMe/web
```

Do **not** expose the repository root:

```text
/path/to/GiggleMe
```

The repository root may contain `settings.py` and other private deployment files that must never be served over HTTP.

### Requirements

The web host needs:

- a PHP-capable web server
- PHP with MySQL connectivity
- access to the same MySQL database used by GiggleMe
- a private web-side database configuration
- HTTPS before exposing the site publicly

No special rewrite rules have been confirmed as required, so the supplied examples intentionally use a simple PHP document-root configuration rather than inventing application routing that the code may not need.

### Apache example

An example Apache virtual host is included at:

```text
deploy/apache-giggleme.conf.example
```

Copy it to the appropriate Apache site-config directory for your system, then edit:

- `ServerName`
- `DocumentRoot`
- the matching `<Directory>` path

The important part is that both paths point specifically to `GiggleMe/web`.

After enabling the site, reload Apache using the normal method for your distribution.

### nginx example

An example nginx server block is included at:

```text
deploy/nginx-giggleme.conf.example
```

Edit:

- `server_name`
- `root`
- the PHP-FPM socket in `fastcgi_pass`

The PHP-FPM socket name varies by installed PHP version and distribution, so the example deliberately contains:

```text
/run/php/phpX.Y-fpm.sock
```

rather than pretending every Linux machine has the same PHP installation.

### Web application configuration

The bot-side configuration is documented through `settings.example.py`.

The web-side source still needs one final configuration pass before this part of deployment can be considered fully reproducible. In particular, identify where the PHP application currently gets:

- MySQL host
- MySQL username
- MySQL password
- MySQL database name
- any Discord/OAuth credentials, if used
- any public/callback URL values, if used

If any of those values are currently hard-coded or stored in a local untracked PHP file, preserve the real local file as private and add a sanitized `.example` equivalent to the repository.

Do not invent new configuration names merely for documentation. The example file should mirror what the PHP code actually consumes.

### Verify the web interface

Once the site loads:

1. Confirm PHP pages render without errors.
2. Confirm the site can read from the GiggleMe database.
3. Create or edit a harmless test scheduled message through the website.
4. Confirm the expected row/change is written to MySQL.
5. Confirm the running bot notices the web-side change through `request_queue`.
6. Confirm the bot continues polling after the queue entry is processed.

If the website works but the bot does not notice changes, check the bot logs and the contents of `request_queue` before treating it as a web-server problem.

### HTTPS

If the site is reachable from the public Internet, terminate HTTPS at the web server or a trusted reverse proxy. Database credentials and any Discord authentication data must never be sent over an unencrypted public HTTP connection.

## How scheduling is stored

The `messages` table is shared by several message-like features.

The current application distinguishes message types partly through `delivery_time`:

- `delivery_time >= 0`: scheduled message
- `delivery_time = -2`: auto-reply
- other/null cases: template behavior

This is existing application behavior and should not be changed casually because existing database rows depend on it.

Scheduled messages can also contain repeat information, a repeat-until time, and `special_handling` flags used by particular delivery behaviors.

## Database notes

The schema contains nine tables and no MySQL triggers or scheduled MySQL events.

Several relationships are maintained by application logic rather than MySQL foreign-key constraints. Guild, user, channel, and template IDs are related across tables without declared foreign keys.

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
│   ├── giggleme.service.example       # example systemd unit
│   ├── apache-giggleme.conf.example   # optional Apache web host
│   └── nginx-giggleme.conf.example    # optional nginx web host
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
- keep Auto Reply configuration on slash commands; if the privileged `MESSAGE_CONTENT` intent is ever removed, remove or redesign the trigger-matching feature that depends on ordinary message text
- add a sanitized example for the web application's own database/auth configuration
- split the large `on_message` command dispatcher into focused command handlers
- add database migrations for future schema changes
- normalize magic values and flags into named types/constants
- modernize Python and third-party dependencies in a controlled upgrade
- add automated tests around scheduling and persistence before large structural changes

## License

GiggleMe is released under the MIT License.
