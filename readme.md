# FairShare Bot

FairShare is a Telegram bot built with Python using the `pyTelegramBotAPI` library. It is designed to help users track and manage shared expenses in a group. The bot allows users to register, add expenses, settle debts, and check balances within the single group.

## About

FairShare Bot is a simple, yet powerful tool for managing shared expenses. Whether it's a group of friends, coworkers, or housemates, this bot helps to ensure that everyone pays their fair share. Users can:
- Register themselves and other users.
- Add shared expenses.
- Split expenses equally among all group members.
- Keep track of who owes whom.
- Settle debts by making payments.
- Revert any transaction if needed.
- View transaction history and balances.

## Functionalities

### Commands

1. **/register**  
   Registers a user in the group. If no username is provided, it uses the message sender's username.
   - Usage: `/register {username}`  
   - Example: `/register john_doe`

2. **/add**  
   Adds an expense that should be divided equally among all users in the group.
   - Usage: `/add {amount}`  
   - Example: `/add 100`  
   - This will divide 100 equally among all users in the group.

3. **/addto**  
   Adds an expense paid by a specific user and divides it among all other users.
   - Usage: `/addto {userpaid} {amount}`  
   - Example: `/addto john_doe 100`

4. **/pay**  
   Allows one user to pay another user a certain amount to settle the debt.
   - Usage: `/pay {username} {amount}`  
   - Example: `/pay john_doe 50`

5. **/check**  
   Checks the balance for a user. If no username is specified, it checks the balance for the sender of the message.
   - Usage: `/check {username}` or just `/check`
   - Example: `/check` or `/check john_doe`

6. **/revert**  
   Reverts a previously made transaction (only works if the transaction ID is specified).
   - Usage: `/revert`
   - Example: `/revert` (reply to a transaction message with this command)

7. **/all**  
   Displays all transactions made in the group, with their details.
   - Usage: `/all`

8. **/my**  
   Displays all transactions made by the sender of the message.
   - Usage: `/my`

9. **/users**  
   Lists all registered users in the group.
   - Usage: `/users`

10. **/remove**  
    Removes a user from the group (only available to admins).
    - Usage: `/remove {username}`  
    - Example: `/remove john_doe`

## Requirements

To run this project, you need Python 3.7 or later and the following dependencies:

- `pyTelegramBotAPI` for interacting with the Telegram Bot API.
- `python-dotenv` to manage environment variables.
- `re` and `datetime` for regular expression operations and managing timestamps.

You can install the required dependencies using `pip`:

```bash
pip install pyTelegramBotAPI python-dotenv
```

## Setup and Running the Bot

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/fairshare-bot.git
   ```

2. **Install dependencies:**

   Navigate to the project directory and install the required Python packages:

   ```bash
   pip install pyTelegramBotAPI python-dotenv
   ```

3. **Create a `.env` file:**

   In the root of the project directory, create a `.env` file to store your bot's token. The file should look like this:

   ```
   BOT_TOKEN=your-telegram-bot-token-here
   ```

4. **Run the bot:**

   Execute the bot script to start the bot:

   ```bash
   python fairshare.py
   ```

   The bot should now be running and you can start interacting with it on Telegram!


## License

This project is licensed under the MIT License - see the LICENSE file for details.

For any questions or suggestions, feel free to open an issue or create a pull request!

---

### Instructions:
- Replace the `BOT_TOKEN` with your actual Telegram bot token in the `.env` file.
- The bot script can be run using `python fairshare.py`.