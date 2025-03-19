import os
import re
import telebot
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Store group expenses and user balances (in-memory storage)
transaction_ledger = []  # To store transactions in the group
users_in_group = set()  # To track users who have interacted with the bot
user_balances = {}  # 2D dictionary to track each user's balance with every other user

# Function to initialize user balances with other users
def initialize_user_balance(username):
    if username not in user_balances:
        user_balances[username] = {}
    for user in users_in_group:
        if user != username:
            if user not in user_balances[username]:
                user_balances[username][user] = 0
            if username not in user_balances[user]:
                user_balances[user][username] = 0

# Function to generate a unique transaction ID
def generate_transaction_id():
    return len(transaction_ledger) + 1

# Function to add expense based on message content
def add_expense_from_message(message):
    try:
        # Extract numbers from the message (looking for a valid number)
        amount = None
        amounts = re.findall(r"\b\d+\.\d+|\d+\b", message.text)  # Find any numbers in the message
        
        # If no numbers were found or the amount is invalid, return
        if not amounts:
            return None
        
        # Convert the first number found into a float
        amount = float(amounts[0])
        
        # Check that the amount is positive
        if amount <= 0:
            return None
        
        # If a user wrote the amount, they paid this amount, others should pay them
        amount_per_user = amount / len(users_in_group)  # Divide the amount equally among all members

        # Update the balances for all users in the group
        for user in users_in_group:
            if user != message.from_user.username:
                if user not in user_balances:
                    user_balances[user] = {}
                if message.from_user.username not in user_balances[user]:
                    user_balances[user][message.from_user.username] = 0
                user_balances[user][message.from_user.username] -= amount_per_user

        # The user who paid is owed the full amount minus their own share
        if message.from_user.username not in user_balances:
            user_balances[message.from_user.username] = {}
        for user in users_in_group:
            if user != message.from_user.username:
                if user not in user_balances[message.from_user.username]:
                    user_balances[message.from_user.username][user] = 0
                user_balances[message.from_user.username][user] += amount_per_user
        
        # Record the transaction in the ledger
        transaction_id = generate_transaction_id()
        transaction_ledger.append({
            'id': transaction_id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'amount': amount,
            'payer': message.from_user.username,
            'users': list(users_in_group)
        })

        return amount
    except ValueError:
        return None

@bot.message_handler(commands=['add'])
def add_expense(message):
    command = message.text.split(' ', 1)
    if len(command) != 2:
        bot.reply_to(message, "Incorrect format. Use /add {amount} or /add {amount} user1,user2,...")
        return

    # Try to extract the amount and users
    try:
        amount_and_users = command[1].split(" ")
        amount = float(amount_and_users[0])  # First part is the amount
        users = amount_and_users[1] if len(amount_and_users) > 1 else ""
        
        # Validate that the amount is positive
        if amount <= 0:
            bot.reply_to(message, "Amount should be greater than zero.")
            return

    except ValueError:
        bot.reply_to(message, "Invalid amount or format. Please check the input.")
        return

    # If no specific users are mentioned, use all registered users
    if not users:
        users_list = list(users_in_group)
    else:
        users_list = [user.strip() for user in users.split(',')]  # Parse the comma-separated usernames

    # Validate that the users are registered
    for user in users_list:
        if user not in users_in_group:
            bot.reply_to(message, f"User {user} is not registered.")
            return

    # Calculate the amount each user will either receive or pay
    amount_per_user = amount / len(users_list)

    # Update the balances for each user
    for user in users_in_group:
        if user != message.from_user.username and user not in users_list:
            # Reset the balances to reflect that the user isn't part of the transaction
            user_balances[user][message.from_user.username] = 0

    # Update balances for the selected users
    for user in users_list:
        if user != message.from_user.username:
            if user not in user_balances[message.from_user.username]:
                user_balances[message.from_user.username][user] = 0
            user_balances[message.from_user.username][user] += amount_per_user  # A pays B

        if message.from_user.username not in user_balances[user]:
            user_balances[user][message.from_user.username] = 0
        user_balances[user][message.from_user.username] -= amount_per_user  # B receives from A

    # Record the transaction in the ledger
    transaction_id = generate_transaction_id()
    transaction_ledger.append({
        'id': transaction_id,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'amount': amount,
        'payer': message.from_user.username,
        'users': users_list
    })

    # Respond with the transaction details
    transaction = transaction_ledger[-1]
    transaction_message = (
        f"Transaction ID: {transaction['id']}\n"
        f"Date: {transaction['date']}\n"
        f"Amount: {transaction['amount']}\n"
        f"Paid By: {transaction['payer']}\n"
        f"Users: {', '.join(transaction['users'])}"
    )
    bot.reply_to(message, transaction_message)

# Command to register a user
@bot.message_handler(commands=['register'])
def register_user(message):
    command = message.text.split(' ', 1)
    username = message.from_user.username

    # If user provides another username, use it
    if len(command) == 2:
        username = command[1]

    if username not in users_in_group:
        users_in_group.add(username)
        # Initialize balance for the new user with all other users
        initialize_user_balance(username)
        bot.reply_to(message, f"User {username} registered successfully.")
    else:
        bot.reply_to(message, f"User {username} is already registered.")

# Function to add expense on behalf of another user (for all members)
@bot.message_handler(commands=['addto'])
def add_expense_to_user(message):
    command = message.text.split(' ', 2)
    if len(command) != 3:
        bot.reply_to(message, "Incorrect format. Use /addto {userpaid} {amount}")
        return
    
    user_paid = command[1]
    try:
        amount = float(command[2])
    except ValueError:
        bot.reply_to(message, "Invalid amount. Please enter a valid number.")
        return

    # Check if the user paid is registered
    if user_paid not in users_in_group:
        bot.reply_to(message, f"User {user_paid} is not registered in the tracker. Use /register {user_paid} to register.")
        return

    # Check if the amount is valid
    if amount <= 0:
        bot.reply_to(message, "Amount should be greater than zero.")
        return

    # Calculate the amount per user (including the user who paid)
    amount_per_user = amount / len(users_in_group)

    # Update the balances for all users (consistent handling of the balances)
    for user in users_in_group:
        if user not in user_balances:
            user_balances[user] = {}
        if user_paid not in user_balances[user]:
            user_balances[user][user_paid] = 0
        
        # If the user paid, they receive the full amount, and others owe them
        if user == user_paid:
            user_balances[user][user_paid] += amount - amount_per_user  # The paid amount minus their own share
        else:
            user_balances[user][user_paid] -= amount_per_user  # Other users owe the one who paid

        # Ensure the balance is stored in the reverse direction (this ensures consistency)
        if user_paid not in user_balances[user]:
            user_balances[user][user_paid] = 0
        
        if user != user_paid:
            user_balances[user_paid][user] = user_balances.get(user_paid, {}).get(user, 0) + amount_per_user

    # Record the transaction
    transaction_id = generate_transaction_id()
    transaction_ledger.append({
        'id': transaction_id,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'amount': amount,
        'payer': user_paid,
        'users': list(users_in_group)
    })

    # Respond to the user with the transaction details
    transaction = transaction_ledger[-1]
    transaction_message = (
        f"Transaction ID: {transaction['id']}\n"
        f"Date: {transaction['date']}\n"
        f"Amount: {transaction['amount']}\n"
        f"Paid By: {transaction['payer']}\n"
        f"Users: {', '.join(transaction['users'])}"
    )
    bot.reply_to(message, transaction_message)

# Command to make a payment
@bot.message_handler(commands=['pay'])
def pay_debt(message):
    command = message.text.split(' ', 2)
    if len(command) != 3:
        bot.reply_to(message, "Incorrect format. Use /pay {username} {amount}")
        return

    try:
        payer = message.from_user.username
        payee = command[1]
        amount = float(command[2])
        
        if payer not in user_balances or payee not in user_balances:
            bot.reply_to(message, "Both users must be registered.")
            return
        
        if user_balances[payer].get(payee, 0) < amount:
            bot.reply_to(message, f"You don't owe {payee} that much!")
            return
        
        # Update the balances
        user_balances[payer][payee] -= amount
        user_balances[payee][payer] += amount

        # Record the payment transaction
        transaction_id = generate_transaction_id()
        transaction_ledger.append({
            'id': transaction_id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'amount': amount,
            'payer': payer,
            'users': [payer, payee]
        })

        # Respond with the transaction details
        transaction = transaction_ledger[-1]
        transaction_message = (
            f"Transaction ID: {transaction['id']}\n"
            f"Date: {transaction['date']}\n"
            f"Amount: {transaction['amount']}\n"
            f"Paid By: {transaction['payer']}\n"
            f"Users: {', '.join(transaction['users'])}"
        )
        bot.reply_to(message, transaction_message)

    except ValueError:
        bot.reply_to(message, "Invalid amount. Please provide a valid number.")


# Command to revert a transaction
@bot.message_handler(commands=['revert'])
def revert_transaction(message):
    if message.reply_to_message and 'Transaction ID:' in message.reply_to_message.text:
        try:
            # Get transaction ID from the replied message
            transaction_id = int(re.findall(r"Transaction ID: (\d+)", message.reply_to_message.text)[0])
            # Find the transaction in the ledger
            transaction = next((txn for txn in transaction_ledger if txn['id'] == transaction_id), None)

            if not transaction:
                bot.reply_to(message, f"No transaction found with ID {transaction_id}.")
                return

            # Revert the transaction
            for user in transaction['users']:
                if user != transaction['payer']:
                    if user not in user_balances:
                        user_balances[user] = {}
                    if transaction['payer'] not in user_balances[user]:
                        user_balances[user][transaction['payer']] = 0
                    user_balances[user][transaction['payer']] += transaction['amount'] / len(transaction['users'])

            # Update the payer's balance
            if transaction['payer'] not in user_balances:
                user_balances[transaction['payer']] = {}
            for user in transaction['users']:
                if user != transaction['payer']:
                    if user not in user_balances[transaction['payer']]:
                        user_balances[transaction['payer']][user] = 0
                    user_balances[transaction['payer']][user] -= transaction['amount'] / len(transaction['users'])

            # Remove the transaction from the ledger
            transaction_ledger.remove(transaction)

            bot.reply_to(message, f"Transaction ID {transaction_id} has been reverted.")

        except Exception as e:
            bot.reply_to(message, f"Error while reverting: {e}")
    else:
        bot.reply_to(message, "Please reply to the transaction message or provide the transaction ID to revert.")

@bot.message_handler(commands=['check'])
def check_balance(message):
    # Parse the command and check if a username is specified
    command = message.text.split(' ', 1)
    
    # If no username is provided, use the sender's username
    if len(command) == 1:
        username = message.from_user.username
    else:
        username = command[1]
    
    # Check if the user is registered
    if username not in user_balances:
        bot.reply_to(message, f"{username} is not registered.")
        return

    # Initialize variables to track the total amount the user has to receive or pay
    total_receive = 0
    total_pay = 0
    balance_report = []

    # Iterate through each user and calculate balances
    for user, balance in user_balances[username].items():
        if user == username:
            continue
        if balance > 0:
            balance_report.append(f"Receive {balance:.2f} from {user}")
            total_receive += balance
        elif balance < 0:
            balance_report.append(f"Pay {-balance:.2f} to {user}")
            total_pay += -balance

    # Provide a message based on the user's balances
    if not balance_report:
        balance_report.append("No transactions recorded yet.")

    # Create the final balance report
    balance_report.append(f"\nTotal to Receive: {total_receive:.2f}")
    balance_report.append(f"Total to Pay: {total_pay:.2f}")

    # Send the reply message with the balance details
    bot.reply_to(message, f"Balance details for {username}:\n" + "\n".join(balance_report))

# Command to show all transactions in the group with details
@bot.message_handler(commands=['all'])
def show_all_transactions(message):
    if not transaction_ledger:
        bot.reply_to(message, "No transactions have been recorded.")
        return
    
    report = []
    for transaction in transaction_ledger:
        report.append(f"Date: {transaction['date']}\nTransaction ID: {transaction['id']}\nAmount: {transaction['amount']}\nPaid By: {transaction['payer']}\nUsers: {', '.join(transaction['users'])}")
    
    # Join the report lines and send to user
    report_message = "\n\n".join(report)
    bot.reply_to(message, report_message)

# Command to show transactions done by the current user
@bot.message_handler(commands=['my'])
def show_my_transactions(message):
    user_name = message.from_user.username
    report = []
    
    for transaction in transaction_ledger:
        if transaction['payer'] == user_name:
            report.append(f"Date: {transaction['date']}\nTransaction ID: {transaction['id']}\nAmount: {transaction['amount']}\nPaid By: {transaction['payer']}\nUsers: {', '.join(transaction['users'])}")

    if not report:
        report.append("No transactions recorded.")
    
    # Join the report lines and send to user
    report_message = "\n\n".join(report)
    bot.reply_to(message, f"Transaction details of {user_name}:\n\n" + report_message)

# Command to show all users in the group
@bot.message_handler(commands=['users'])
def list_users(message):
    if not users_in_group:
        bot.reply_to(message, "No users have been registered yet.")
        return
    
    user_list = "\n".join(users_in_group)
    bot.reply_to(message, f"Registered users:\n\n{user_list}")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    # Get the chat admins list to check if the sender is an admin
    try:
        chat_admins = bot.get_chat_administrators(message.chat.id)
        is_admin = any(admin.user.username == message.from_user.username for admin in chat_admins)
        
        if not is_admin:
            bot.reply_to(message, "You do not have permission to remove users.")
            return
    except Exception as e:
        bot.reply_to(message, f"Error checking admin status: {e}")
        return

    # Split the command and get the username to remove
    command = message.text.split(' ', 1)
    if len(command) != 2:
        bot.reply_to(message, "Incorrect format. Use /remove {username}.")
        return
    
    username = command[1]
    
    if username in users_in_group:
        users_in_group.remove(username)
        # Remove the user's balance info
        if username in user_balances:
            del user_balances[username]
        
        # Remove the user's balances from others
        for other_user in user_balances:
            if username in user_balances[other_user]:
                del user_balances[other_user][username]
        
        bot.reply_to(message, f"User {username} has been removed from the group.")
    else:
        bot.reply_to(message, f"User {username} is not registered in the group.")

bot.infinity_polling()