# Sobornyi Bot

Telegram bot to control the Sobornyi group.

In order to run it:

1. Create a bot here: [@BotFather](https://t.me/BotFather).
2. Create a chat group in Telegram.
3. Create a channel in Telegram.
4. Add your bot to both the group and the channel as admin with full rights.
5. Add `config/settings.local.yml` with settings for the environments (`dev` and `prod`).
6. Add bot token to `config/.secrets.local.yml`.
7. Set up the environment: `make init`
8. Activate the environment: `conda activate telegram-bot`.
9. Run the bot: `make debug` (dev) or `make run` (prod).
10. Enjoy!

Hint: in order to get `chat_id` run `/info` command for the bot in that chat.

## Data Migration

When updating the model structure, you may need to migrate your persistent data. The bot includes a migration tool for this purpose:

```bash
# Migrate the data
make migrate
```

For more information about the migration tool, see [tools/README.md](tools/README.md).
