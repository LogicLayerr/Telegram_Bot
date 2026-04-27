# Description

This bot is designed to conveniently store useful links in one place.

Imagine that you have found a website with important information and want to save it so that you can return and re-read it later. Copy the link and send it to the bot. He saves it in the database. Do you want to give the link a name? Click "Add a name" and send what you want. The bot will save the name, and your text will be displayed instead of the link.

You can add the same link as many times as you want. If you no longer need the copies, instead of deleting each link individually, click "Delete duplicates." The bot will only keep the first duplicate. You can also delete all links with a single command.

### Bot functions:

1. Registration and sending links: the bot registers a new user in the database and sends all the links they have added. If there are no links, it will write "It's empty for now."
2. Adding a link: the user sends a link to the chat, and the bot adds it to the database. This function is only available after function 1 for the first time.
3. Linking a name to a link: the bot adds the name that the user sends, linking it to the link in the database.
4. Delete links: the user selects a link, and the bot deletes it from the database.
5. Delete duplicates: the bot deletes all duplicate links, leaving only the original (first) link.
6. /start — the bot turns on and greets the user.
7. /help — the bot sends a message with useful information.
8. /delete_all — the bot deletes all the user's links from the database.

# Instructions for use:

The bot does not work around the clock, but you can send the command /start, and it will respond as soon as it is launched.

Link to the bot in Telegram: https://t.me/MyIsbrannoeBot

If you want to install this bot on your computer, follow the instructions below.

# Technology stack:

* Python 3.14.13
* Virtual environment venv (installation - “python -m venv venv”)
* HTML (import html)
* pyTelegramBotAPI (installation - “pip install pyTelegramBotAPI” )
* psycopg2 (installation - “pip install psycopg2” )
* PostgreSQL:
  * pgAdmin 4:
    * TGBOT database:
    * The database structure is located in the SchemTGBOT file
    * 3 Tables:
      1. Chats:
         * Columns:
            1. chat_id
            2. message_id
      2. links:
         * Columns:
            1. id
            2. link_text
            3. chat_id
      3. links_name:
         * Columns:
            1. links_name
            2. links_id

# Installation instructions:

1. Create a Telegram bot using @BotFather.
2. Install Python 3.
3. Install a code editor (such as VS Code).
4. Open the BOT_E file in the code editor.
5. Install the venv virtual environment (run "python -m venv venv" in the terminal).
6. Install pyTelegramBotAPI (run "pip install pyTelegramBotAPI" in the terminal).
7. Install psycopg2 (send "pip install psycopg2" to the terminal).
8. Insert the token received from @BotFather into the 7th line of the code instead of *** .
9. Install PostgreSQL + pgAdmin 4.
10. Create a new database.
11. Right-click on the database → Query tool → Click on the open file button (folder) → open the SchemTGBOT file.
12. Run the code in the code editor and use the bot on Telegram.

If I forgot something, please contact me.  
