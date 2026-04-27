import telebot
from telebot import types
import psycopg2 
from psycopg2 import pool
import html

TOKEN = "***"
bot = telebot.TeleBot(TOKEN)

db_pool = psycopg2.pool.SimpleConnectionPool(
    1, 10,
    host = 'localhost',
    user = 'postgres',
    password = 'postgres',
    port = 5432,
    dbname = 'TGBOT'
)


def get_links_text(chat_id: int) -> str:
    """Вспомогательная функция для сборки текста списка ссылок"""
    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT link_text, links_name FROM links 
                   LEFT OUTER JOIN links_name ON links_name.links_id = links.id
                   WHERE chat_id = %s
                   ''', (chat_id,))
    result = cursor.fetchall()
    cursor.close()
    db_pool.putconn(conn)
    if not result:
        return "📋 Список ссылок:\n\nПока пусто."
    
    text = "📋 Список ссылок:\n\n"
    for y, row in enumerate(result, 1):
        text += f'{y}. <a href="{row[0]}">{row[1]}</a>\n'
    return text        
    
@bot.message_handler(commands=['start'])
def main(message: telebot.types.Message):
    """Сообщение после /start"""
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Отправить Мастер-Сообщение')
    btn2 = types.KeyboardButton('Удалить дубликаты')
    btn3 = types.KeyboardButton('/help')
    btn4 = types.KeyboardButton('Удалить ссылку')
    btn5 = types.KeyboardButton('Добавить название ссылке')
    markup.row(btn1, btn4)
    markup.row(btn2, btn5)
    bot.send_message(message.chat.id, f"Бот активирован. \nЧем могу помочь, {message.from_user.first_name}?", reply_markup=markup)
    
@bot.message_handler(commands=['help'])
def help(message: telebot.types.Message):
    """Полезная информация"""
    bot.send_message(message.chat.id, 'Чтобы добавить ссылку, просто пришлите ее мне!\n\nЕсли вы хотите поменять название ссылки, удалите ее и заново добавьте.\nЕсли не указать название, то оно будет = "None"\n\n📝Список доступных комманд: \n/start\n/help\n/delete_all')
    
@bot.message_handler(commands=['delete_all'])
def delete_all_links(message: telebot.types.Message):
    """Удаляет все ссылки у пользователя"""
    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute('''
                   DELETE FROM links
                   WHERE chat_id = %s
                   ''', (message.chat.id,))
    conn.commit()
    cursor.close()
    db_pool.putconn(conn)
    bot.send_message(message.chat.id, 'Ссылки удалены')
    
@bot.message_handler(func=lambda message: message.text and ('http://' in message.text or 'https://' in message.text))
def handle_links(message: telebot.types.Message):
    """Добавляет значение в мастер-сообщение"""
    chat_id = message.chat.id
    link_text = message.text
    
    conn = db_pool.getconn()
    cursor = conn.cursor()
    
    # Проверяем, есть ли запись о главном сообщении
    cursor.execute('SELECT message_id FROM chats WHERE chat_id = %s', (chat_id,))
    result = cursor.fetchone()
    message_id = result[0]

    try:
        cursor.execute('''
                       INSERT INTO links (chat_id, link_text)
                       VALUES (%s, %s)
                       ''', (chat_id, link_text,))
        conn.commit()
        # Получаем обновленный текст (учитывая новую ссылку)
        new_text = get_links_text(chat_id)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=new_text,
            parse_mode='HTML',
            disable_web_page_preview=True
            )
        bot.reply_to(message, "Ссылка добавлена")
    except Exception as e: 
        bot.reply_to(message, f"Ошибка: {e}")
        print(e)
    finally:
        cursor.close()
        db_pool.putconn(conn)

def generate_dynamic_buttonsDEL(button_texts: str, row_width: int,rows) -> telebot.types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for i, row in enumerate(rows, 1):
        link_id = row[0]
        link_text = row[1]

        button = types.InlineKeyboardButton(
            text=f"{i}. {link_text[:20]}",  # что видит пользователь 
            callback_data='DEL' + str(link_id),  # что уходит в код
            style= 'danger'  #Красный цвет
        )
        markup.add(button)
    return markup   

def generate_dynamic_buttonsADD(button_texts: str, row_width: int,rows) -> telebot.types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for i, row in enumerate(rows, 1):
        link_id = row[0]
        link_text = row[1]

        button = types.InlineKeyboardButton(
            text=f"{i}. {link_text[:20]}",  # что видит пользователь 
            callback_data='ADD' + str(link_id), # что уходит в код
            style= 'primary' #Синий цвет
        )
        markup.add(button)
    return markup   

@bot.message_handler()
def dispetcher(message: telebot.types.Message):
    """Вызывает функции, в ответ на сообщения"""
    text = message.text.lower()
    if text == 'отправить мастер-сообщение':
        send_message(message)
    elif text == 'удалить дубликаты':
        delete_copy(message)
    elif text == 'удалить ссылку':
        delete_link(message)
    elif message.text.lower() == 'добавить название ссылке': 
        add_name(message)   
               
def send_message(message: telebot.types.Message):
    """Отправляет мастер-сообщение"""
    chat_id = message.chat.id
    current_text = get_links_text(chat_id)
    msg = bot.send_message(chat_id, current_text, parse_mode='HTML', disable_web_page_preview=True)
        
    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (chat_id, message_id) 
        VALUES (%s, %s) 
        ON CONFLICT(chat_id) DO UPDATE SET message_id = excluded.message_id
     ''', (chat_id, msg.message_id,))  
    conn.commit()
    cursor.close()
    db_pool.putconn(conn)
    
def delete_copy(message: telebot.types.Message):
    """Удаляет копии ссылок, кроме самой старой"""
    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute('''
                   DELETE FROM links
                   USING (
                        SELECT MIN(id) as id, link_text 
                        FROM links 
                        GROUP BY link_text HAVING COUNT(*) > 1
                    ) AS t1
                    WHERE links.id > t1.id AND links.link_text = t1.link_text;
                   ''')
    conn.commit()
    cursor.close()
    db_pool.putconn(conn)
    bot.send_message(message.chat.id, 'Дубликаты ссылок удалены')
    
def delete_link(message: telebot.types.Message):
    """Предоставляет пользователю выбор, какую ссылку удалить"""
    chat_id = message.chat.id
    
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT link_text FROM links WHERE chat_id = %s', (chat_id,))
        result = cursor.fetchall()
        text = ""
        for i in enumerate(result, 1):
            text += f'{i}'
        button_text = list(text)
        
        cursor.execute('SELECT id, link_text FROM links WHERE chat_id = %s', (chat_id,))
        rows = cursor.fetchall()   
        markup = generate_dynamic_buttonsDEL(button_text, 1, rows)   
        bot.send_message(chat_id, 'Выберете номер ссылки, которую желаете удалить', reply_markup=markup) 
    except Exception as e:
        bot.send_message(chat_id, f'Ошибка при загрузке ссылок: {e}')
    finally:
        cursor.close()
        db_pool.putconn(conn)
        
@bot.callback_query_handler(func=lambda call: call.data.startswith('DEL'))
def callback_delete_link(call: telebot.types.CallbackQuery):
    """Удаляет ссылку, выбранную пользователем"""
    conn = db_pool.getconn()
    cursor = conn.cursor()
    call_data = int(call.data.replace('DEL',''))
    chat_id = call.message.chat.id
    try:
        cursor.execute('''
                        DELETE FROM links
                        WHERE id = %s AND chat_id = %s
                        ''', (call_data, chat_id,)) 
        conn.commit()
        if cursor.rowcount == 0:
            bot.answer_callback_query(call.id, 'Ссылка не найдена')
        else:
            bot.answer_callback_query(call.id, 'Ссылка удалена')
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.id,
                text='Ссылка удалена'
            )
    except Exception as e:
        bot.answer_callback_query(call.id, f'Ошибка: {e}')
        conn.rollback()
    finally:
        cursor.close()
        db_pool.putconn(conn)   
         
def add_name(message: telebot.types.Message):
    """Предоставляет пользователю выбор, какой ссылке добавить название"""
    chat_id = message.chat.id
        
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT link_text FROM links WHERE chat_id = %s', (chat_id,))
        result = cursor.fetchall()
        text = ""
        for i in enumerate(result, 1):
            text += f'{i}'
        button_text = list(text)
        
        cursor.execute('SELECT id, link_text FROM links WHERE chat_id = %s', (chat_id,))
        rows = cursor.fetchall()   
        markup = generate_dynamic_buttonsADD(button_text, 1, rows)   
        bot.send_message(chat_id, 'Выберете ссылку, которой желаете добавить название', reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f'Ошибка при загрузке ссылок: {e}')
    finally:
        cursor.close()
        db_pool.putconn(conn)
    
user_pending_name = {} #Временное хранилище
     
@bot.callback_query_handler(func=lambda call: call.data.startswith('ADD'))
def callback_add_name(call: telebot.types.CallbackQuery):
    """Запоминает выбор поьзователя и спрашивает какое название вставить"""       
    chat_id = call.message.chat.id
    links_id = int(call.data.replace('ADD',''))
        
    # Сохраняем ID ссылки для текущего пользователя
    user_pending_name[chat_id] = links_id
    
    bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text= 'Введите название для этой ссылки')
    bot.answer_callback_query(call.id, 'В процессе...')
    bot.register_next_step_handler(call.message, add_link_name)
    
@bot.message_handler(func=lambda message: message.chat.id in user_pending_name)
def add_link_name(message: telebot.types.Message):
    """Добавляет название для ссылки"""
    chat_id = message.chat.id
    link_id = user_pending_name.pop(chat_id)
    new_name = message.text.strip()
    if not new_name:
        bot.send_message(chat_id, 'Ошибка! Введите текстовое значение.')
        return
    
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute('''
                       INSERT INTO links_name(links_name, links_id)
                       VALUES(%s, %s)
                       ''', (new_name, link_id,))
        conn.commit()
        if cursor.rowcount == 0:
            bot.send_message(chat_id, 'Ссылка не найдена или недоступна.')
        else:
            bot.send_message(chat_id, 'Название успешно обновлено!')
    except Exception as e:
        bot.send_message(chat_id, f'Ошибка при сохранении названия: {e}')
        conn.rollback()
    finally:
        cursor.close()
        db_pool.putconn(conn)       
           
if __name__ == '__main__':
    print("Бот запущен")
    bot.infinity_polling()