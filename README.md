# sobornyi-bot
Telegram bot to control the Sobornyi group.

In order to test/play with it:
1. Create a bot here: `@BotFather`
2. Set up the environment variable:
- SOBORNYI_BOT_API_TOKEN
3. Create a test group space in Telegram.
4. Add your bot to the group.
5. Set up the dev environment with `conda env create -f environment.yml && conda activate telegram`.
6. Run the bot with `make debug`.
7. Type `\info` in your group.
8. Set up the environment variables:
- TELEGRAM_ADMIN_ID
- TELEGRAM_SOBORNYI_CHAT_ID
9. Rerun the bot and enjoy!
