# Sobornyi Bot
Telegram bot to control the Sobornyi group.

In order to run it:
1. Create a bot here: [@BotFather](https://t.me/BotFather).
1. Create a chat group in Telegram.
1. Create a channel in Telegram.
1. Add your bot to both the group and the channel as admin with full rights.
1. Add `config/settings.local.yml` with settings for the environments (`dev` and `prod`).
1. Add bot token to `config/.secrets.local.yml`.
1. Set up the environment: `make init`
1. Activate the environment: `conda activate telegram-bot`.
1. Run the bot: `make debug` (dev) or `make run` (prod).
1. Enjoy!

Hint: in order to get `chat_id` run `/info` command for the bot in that chat.