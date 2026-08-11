# GiggleMe

GiggleMe is a Discord bot for scheduling messages. Over time it has also grown support for repeating messages, templates, proposals and voting, automatic replies, time-zone handling, VIP/voice-channel behavior, and other server-specific features.

The bot is primarily written in Python and stores its persistent state in MySQL. The repository also contains a PHP-based web interface that uses the same database.

> **Project status**
>
> GiggleMe grew organically around real users and their feature requests. Some parts of the implementation are more general than others, and some behaviors are intentionally specialized. Refactoring is ongoing, so preserving existing behavior is preferred over silently "cleaning up" unusual logic.

## Quick start

A basic deployment requires:

- Python 3 (the current known-working deployment uses Python 3.6.9)
- MySQL or a compatible MySQL server
- a Discord application/bot
- the Python Discord library used by the project
- the Python MySQL connector used by the project
- a local `settings.py` containing deployment-specific settings and secrets

For the optional web interface you will also need a PHP-capable web server.

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

The schema intentionally mirrors the existing production schema. It does not add foreign keys, new indexes, or charset changes that are not already present in the running application.

### Create a dedicated MySQL user

Using a dedicated account is recommended instead of running GiggleMe as MySQL `root`.

Example:

```sql
CREATE USER 'giggleme'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON giggleme.* TO 'giggleme'@'localhost';
FLUSH PRIVILEGES;
```

Adjust the host and permissions to match your deployment.

## 3. Create the Discord bot

Create a Discord application and bot for your deployment, then invite that bot to the servers where you want to use GiggleMe.

The current code creates the Discord client with:

```python
discord.Client(intents=discord.Intents.all())
```

That means a deployment must enable the gateway intents required by the current application in the Discord developer configuration. Reducing GiggleMe to the minimum required intent set is a planned cleanup and is preferable to requesting every intent indefinitely.

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

- `bot_token` — Discord bot token for this GiggleMe instance.
- `bot_owner_id` — Discord user ID of the bot owner.
- `db_user` — MySQL account used by GiggleMe.
- `db_password` — password for that MySQL account.
- `database` — MySQL database name. The supplied `schema.sql` creates `giggleme`.
- `twitter_consumer_key` — consumer/API key used by the Twitter/X-related integration.
- `twitter_consumer_secret` — corresponding consumer/API secret.

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

Those exact direct dependencies are pinned in `requirements.txt` so a new deployment can reproduce the environment before attempting any library or Python upgrades.

Create a virtual environment and install them:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Python 3.6.9 and these package versions are the **known-working baseline**, not a recommendation that new development remain on them forever. Runtime and library modernization should be handled separately and tested as an intentional refactor.

## 6. Make the utility modules importable

`gigglebot.py` imports modules such as `gigdb`, `gigtz`, `giguser`, and `gigguild` directly, while those modules are stored under `util/`.

When running from the repository root, make sure `util/` is on Python's module search path. On Linux/macOS:

```bash
export PYTHONPATH="$PWD/util${PYTHONPATH:+:$PYTHONPATH}"
```

Then start the bot using the startup method expected by your local `settings.py` and current source tree.

If running directly:

```bash
python3 gigglebot.py
```

The repository also includes `restart-giggleme.sh`; deployments already using that script can continue to use it.

## 7. Verify the bot

Once connected to Discord, use:

```text
~giggle help
```

to display GiggleMe's built-in command help.

A good initial smoke test is:

1. Confirm the bot comes online.
2. Run `~giggle help`.
3. Set or verify your timezone.
4. Schedule a test message a few minutes in the future.
5. Confirm the message survives a bot restart and is delivered at the expected time.

Persistent scheduled messages are loaded from MySQL when the bot starts.

## How scheduling is stored

The `messages` table is shared by several message-like features.

The current application distinguishes message types partly through `delivery_time`:

- `delivery_time >= 0`: scheduled message
- `delivery_time = -1`: proposal
- `delivery_time = -2`: auto-reply
- other/null cases: template behavior

This is existing application behavior and should not be changed casually because existing database rows depend on it.

Scheduled messages can also contain repeat information, a repeat-until time, and `special_handling` flags used by particular delivery behaviors.

## Web interface

The repository contains a `web/` directory with a PHP-based interface.

The web application and Python bot communicate through the same MySQL database. Changes made through the web interface can be placed in `request_queue`; the running bot polls that queue and updates its in-memory message state.

A web deployment therefore needs:

- PHP
- access to the same MySQL database used by the bot
- the web application's database configuration
- appropriate web-server configuration and authentication for your environment

The exact Apache/nginx/PHP deployment and authentication model are installation-specific and are not yet fully documented here.

## Database notes

The current production-derived schema contains ten tables and no MySQL triggers or scheduled MySQL events.

Several relationships are maintained by application logic rather than MySQL foreign-key constraints. For example, guild, user, channel, template, and proposal IDs are related across tables without declared foreign keys.

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

## Running as a service

For a permanent Linux deployment, run GiggleMe under a process manager such as `systemd` rather than relying on an interactive shell.

The service should:

- run as an unprivileged account
- start in the GiggleMe repository/application directory
- activate the intended Python virtual environment
- include `util/` in `PYTHONPATH` if needed
- have access to the local `settings.py`
- restart on unexpected failure

The repository's existing `restart-giggleme.sh` can also be used by installations that already depend on it.

## Security

Do not commit:

- Discord bot tokens
- MySQL passwords
- OAuth/API secrets
- production `settings.py`
- private web credentials

Use a dedicated MySQL account for GiggleMe and grant only the access required by the application.

## Project layout

```text
GiggleMe/
├── gigglebot.py          # main Discord bot
├── util/                 # database, parsing, models, timezone and helper modules
├── web/                  # PHP/JavaScript web interface
├── restart-giggleme.sh   # existing restart helper
├── schema.sql            # MySQL schema and required seed data
├── settings.example.py   # safe template for local deployment settings
├── requirements.txt      # pinned known-working Python dependencies
├── README.md
└── LICENSE
```

## Development notes

GiggleMe has accumulated features incrementally over a long period of real-world use. Before removing or simplifying strange-looking behavior, trace where it is used. A branch that appears redundant may exist because one server or user requested a specific behavior.

Useful refactoring goals include:

- replace `discord.Intents.all()` with the minimum required intents
- split the large `on_message` command dispatcher into focused command handlers
- consider moving secrets from Python settings into environment variables
- modernize Python and third-party libraries from the known-working legacy baseline
- add database migrations for future schema changes
- normalize magic values and flags into named types/constants
- add automated tests around scheduling and persistence before large structural changes

## License

GiggleMe is released under the MIT License.
