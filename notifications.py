import psycopg2
from psycopg2 import sql, Error
from datetime import datetime, timedelta, date
from calendar import monthrange
import pytz
import discord
import asyncio
import locale
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set Spanish locale with better error handling
def setup_spanish_locale():
    """Try to set Spanish locale, fallback gracefully if not available"""
    locale_options = [
        'es_ES.UTF-8',      # Linux/Mac standard
        'es_ES',            # Linux/Mac without UTF-8
        'Spanish_Spain.1252', # Windows
        'es',               # Generic Spanish
        'C.UTF-8',          # UTF-8 fallback
        'C'                 # Final fallback
    ]
    
    for loc in locale_options:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            print(f"Locale set to: {loc}")
            return loc
        except locale.Error:
            continue
    
    print("Warning: Could not set Spanish locale, using system default")
    return None

# Setup locale
current_locale = setup_spanish_locale()

# Spanish month names for manual formatting if locale fails
SPANISH_MONTHS = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def format_date_spanish(date_obj):
    """Format date in Spanish, with fallback if locale is not available"""
    try:
        # Try using locale formatting first
        return date_obj.strftime('%d de %B de %Y')
    except:
        # Manual formatting if locale fails
        day = date_obj.day
        month = SPANISH_MONTHS.get(date_obj.month, str(date_obj.month))
        year = date_obj.year
        return f"{day} de {month} de {year}"

# Global bot instance
bot = None

def connect_to_postgres():
    """Connect to PostgreSQL database"""
    try:
        # Database connection parameters from environment variables
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        
        # Create a cursor object
        cursor = connection.cursor()
        
        # Test the connection by getting PostgreSQL version
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print(f"Connected to PostgreSQL: {record[0]}")
        
        return connection, cursor
        
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None, None

def execute_query(connection, cursor, query):
    """Execute a SQL query"""
    try:
        cursor.execute(query)
        
        # If it's a SELECT query, fetch results
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            return results
        else:
            # For INSERT, UPDATE, DELETE, commit the transaction
            connection.commit()
            return cursor.rowcount
            
    except Error as e:
        print(f"Error executing query: {e}")
        connection.rollback()
        return None

def close_connection(connection, cursor):
    """Close database connection"""
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    print("PostgreSQL connection closed")

async def start_discord_bot():
    """Initialize and start the Discord bot"""
    global bot
    
    # Set up bot intents
    intents = discord.Intents.default()
    intents.message_content = True
    
    # Create bot instance
    bot = discord.Client(intents=intents)
    
    # Create an event to wait for bot to be ready
    bot_ready_event = asyncio.Event()
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} connected and ready for notifications')
        bot_ready_event.set()  # Signal that bot is ready
    
    # Start the bot in a background task using token from environment variable
    bot_task = asyncio.create_task(bot.start(os.getenv('DISCORD_BOT_TOKEN')))
    
    # Wait for the bot to be ready
    try:
        await asyncio.wait_for(bot_ready_event.wait(), timeout=10.0)
        print("Bot is ready to send notifications!")
    except asyncio.TimeoutError:
        print("Bot took too long to connect")
        bot_task.cancel()
        raise
    
    return bot_task

async def send_discord_notification(message):
    """Send Discord DM notification using the existing bot connection"""
    global bot
    
    if bot is None or not bot.is_ready():
        print("Bot is not ready or not initialized")
        return
    
    # Get Discord user ID from environment variable
    your_discord_user_id = int(os.getenv('DISCORD_USER_ID'))
    
    try:
        # Get the user object
        user = bot.get_user(your_discord_user_id)
        
        if user is None:
            # Try fetching the user if not in cache
            user = await bot.fetch_user(your_discord_user_id)
        
        if user:
            # Send DM to the user
            await user.send(message)
            print(f"Notification sent: {message}")
        else:
            print(f"Discord user {your_discord_user_id} not found")
                
    except discord.Forbidden:
        print("Cannot send DM - user has DMs disabled or bot is blocked")
    except discord.HTTPException as e:
        print(f"HTTP error sending DM: {e}")
    except Exception as e:
        print(f"Error sending DM: {e}")

async def stop_discord_bot():
    """Stop the Discord bot"""
    global bot
    
    if bot:
        await bot.close()
        print("Discord bot stopped")

def check_user_attendance(conn, cur, users_to_check):
    """Check user attendance and send notifications if needed"""
    select_query = """
        SELECT DISTINCT ON (id_user) attendances.id_user as id_user, users.name, users.lastname, attendances.created_at
        FROM attendances
        JOIN users ON attendances.id_user = users.user_id
        WHERE attendances.id_user = ANY(%s)
        ORDER BY attendances.id_user, attendances.created_at DESC;
    """
    
    try:
        cur.execute(select_query, (users_to_check,))
        results = cur.fetchall()
        
        notifications_to_send = []
        
        if results:
            for row in results:
                user_id, name, lastname, last_attendance = row
                
                # Check if last attendance is older than 2 days
                if last_attendance < (datetime.now(pytz.UTC) - timedelta(days=2)):
                    print(f"Preparing notification for user: {name} {lastname}")
                    formatted_date = format_date_spanish(last_attendance)
                    message = f"**{name} {lastname}** no ha ingresado la asistencia desde el {formatted_date}"
                    notifications_to_send.append(message)
                else:
                    print(f"User {name} {lastname} has recent attendance - no notification needed")
        
        # Check for users not in results (never attended)
        found_user_ids = [row[0] for row in results] if results else []
        missing_users = set(users_to_check) - set(found_user_ids)
        
        if missing_users:
            print(f"Users with no attendance records: {missing_users}")
            # You could add logic here to handle users with no attendance records
        
        print(f"Total notifications prepared: {len(notifications_to_send)}")
        return notifications_to_send
        
    except Error as e:
        print(f"Error checking attendance: {e}")
        return []

def check_old_odts(conn, cur, months_ago):
    select_query = """
        SELECT odts.id_odt, users.name, users.lastname, odts.amount, odts.created_at, currencys.symbol, clients.name, odts.description
            FROM odts
            JOIN users ON users.user_id = odts.id_user
            JOIN currencys USING(id_currency)
            JOIN clients USING(id_client)
            left JOIN closure_odts USING(id_odt)
            WHERE id_closure_odt IS NULL AND odts.created_at < (CURRENT_DATE - INTERVAL %s)
            ORDER BY odts.created_at DESC
    """
    
    try:
        cur.execute(select_query, (f'{months_ago} months',))
        results = cur.fetchall()
        
        notifications_to_send = []
        
        for row in results:
            odt_id, name, lastname, amount, created_at, currency_symbol, client_name, description = row
            
            # Format the message
            formatted_date = format_date_spanish(created_at)
            message = (
                f"\tLa **ODT {odt_id}** de **{name} {lastname}** tiene más de {months_ago} meses abierta:\n"
                f"\tMonto: {currency_symbol}{round(amount,2)}\n"
                f"\tCliente: {client_name}\n"
                f"\tFecha de apertura: {formatted_date}\n"
                f"\tDescripción: {description}\n"
                f"**----------------------------------------------**"
            )
            notifications_to_send.append(message)
        
        print(f"Total ODT notifications prepared: {len(notifications_to_send)}")
        return notifications_to_send
         
    except Error as e:
        print(f"Error checking odts: {e}")
        return []
    

def check_debts(conn, cur):  
    select_query = """
        SELECT loans.id_user, loans.amount, currencys.symbol, users.name, users.lastname
            FROM loans
            JOIN currencys using(id_currency)
            JOIN users ON users.user_id = loans.id_user
            WHERE amount != 0
            ORDER BY amount DESC;
    """
    
    try:
        cur.execute(select_query)
        results = cur.fetchall()
        
        notifications_to_send = []
        
        for row in results:
            id_user, amount, symbol, name, lastname = row
            
            # Format the message
            message = (f"**{name} {lastname}** tiene una deuda de **{symbol}{round(amount,2)}**")
            notifications_to_send.append(message)
        
        print(f"Total debt notifications prepared: {len(notifications_to_send)}")
        return notifications_to_send
         
    except Error as e:
        print(f"Error checking debts: {e}")
        return []
    
def check_low_stocks(conn, cur):  
    select_query = """
        SELECT spendable_stocks.amount as stock, spendable_products.code, spendable_products.mid_stock, storages.name, (spendable_products.mid_stock-spendable_stocks.amount)*spendable_items.cost as cost_for_stock_needed, measures.unit
            FROM spendable_stocks
            JOIN spendable_items USING(id_spendable_item)
            JOIN spendable_products USING(id_spendable_product)
            JOIN storages USING(id_storage)
            JOIN measures USING(id_measure)
            WHERE spendable_stocks.amount < mid_stock
            ORDER BY cost_for_stock_needed DESC
    """
    
    try:
        cur.execute(select_query)
        results = cur.fetchall()
        
        notifications_to_send = []
        
        for row in results:
            stock, code, mid_stock, storage_name, cost_for_stock_needed, unit= row
            
            # Format the message
            message = (
                f"\tEl producto **{code}** en el almacén **{storage_name}** tiene poco stock\n"
                f"\tStock actual: {round(stock,2)} {unit}\n"
                f"\tStock medio: {round(mid_stock,2)} {unit}\n"
                f"\tStock mínimo necesario: {round(mid_stock-stock,2)} {unit}\n"
                f"**----------------------------------------------**"
                       )
            notifications_to_send.append(message)
        
        print(f"Total stock notifications prepared: {len(notifications_to_send)}")
        return notifications_to_send
         
    except Error as e:
        print(f"Error checking stocks: {e}")
        return []


async def main():
    """Main async function to run the entire process"""
    # Connect to database
    conn, cur = connect_to_postgres()
    if conn and cur:
        try:
            # Start Discord bot and wait for it to be ready
            bot_task = await start_discord_bot()

            # Check attendance for specific users from environment variable
            users_to_monitor = [int(x.strip()) for x in os.getenv('USERS_TO_MONITOR', '').split(',') if x.strip()]
            await send_discord_notification('📆 Checking attendance')
            
            attendance_notifications = check_user_attendance(conn, cur, users_to_monitor)
            
            # Send all attendance notifications
            for message in attendance_notifications:
                await send_discord_notification(message)
                # await asyncio.sleep(0.5)  # Small delay between messages

            if(datetime.today().day in [12, 14, 27, (monthrange(date.today().year, date.today().month)[1]-1) ]): #Only check if near to fortnightly closing
                
                await send_discord_notification('💰 Checking debts')
                debts = check_debts(conn, cur)
                for message in debts:
                    await send_discord_notification(message)
                    await asyncio.sleep(0.2)  # Small delay between messages


                await send_discord_notification('📜​ Checking old Open ODTs')
                odt_notifications = check_old_odts(conn, cur, 2)  # Check for ODTs older than 2 months
                # Send all ODT notifications
                for message in odt_notifications:
                    await send_discord_notification(message)
                    await asyncio.sleep(0.2)  # Small delay between messages

                
                await send_discord_notification('📋 Checking low stocks')
                stocks = check_low_stocks(conn, cur)
                for message in stocks:
                    await send_discord_notification(message)
                    await asyncio.sleep(0.2)  # Small delay between messages


            # Wait a moment for all messages to be sent
            await asyncio.sleep(2)

            # Stop the Discord bot
            await stop_discord_bot()
            
            # Cancel the bot task
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
        
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            # Close connection
            close_connection(conn, cur)
    else:
        print("Failed to connect to database")

# Example usage
if __name__ == "__main__":
    asyncio.run(main())