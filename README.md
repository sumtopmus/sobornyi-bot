# sobornyi-bot
Telegram bot to control the Sobornyi group.

In order to play with it:
1. Create a bot here: `@BotFather`.
2. Create a test group (and channel) in Telegram.
3. Add your bot to the group as admin with full rights.
4. Add `config/settings.local.yml` with settings for development environment.
5. Add bot token to `config/.secrets.local.yml` for development environment.
6. Set up the dev environment with `conda env create -f environment.yaml && conda activate telegram-bot`.
7. Run the bot with `make debug`.
8. Enjoy!
