from asyncio import run, sleep
from telebot import types, asyncio_filters
from service_file import bot, operator_bot, MyStates, work_types, regions, check_phone_number
from db import add_user, add_user_info, select_all_user_data, check_if_user_filled, add_queue, select_user_field

def generate_markup(items, selected, prefix):
    markup = types.InlineKeyboardMarkup()
    for i, item in enumerate(items):
        if item in selected:
            markup.add(types.InlineKeyboardButton(text=f'✅ {item}', callback_data=f"{prefix}. 0. {i}"))
        else:
            markup.add(types.InlineKeyboardButton(text=item, callback_data=f"{prefix}. 1. {i}"))
    markup.add(types.InlineKeyboardButton(text="Ок", callback_data=f"{prefix}_ok"))
    return markup

async def toggle_item_in_db(user_id, field, items, add, index):
    selected_item = items[index]
    current_value = select_user_field(user_id, field)
    selected_list = current_value.split(", ") if current_value else []
    if add:
        if selected_item not in selected_list:
            selected_list.append(selected_item)
    else:
        if selected_item in selected_list:
            selected_list.remove(selected_item)
    add_user_info(user_id, section=field, value=", ".join(selected_list))

@bot.message_handler(commands=['start'])
async def start(message):
    username, user_id = message.from_user.username, message.from_user.id
    add_user(username, user_id)
    await bot.send_message(user_id, 'Здравствуйте! Укажите свои контактные данные в нашем боте, чтобы администраторы могли связаться с вами и отправить на участок, который нуждается в помощи')
    await sleep(5)
    await bot.send_message(user_id, 'Продолжая использование бота, вы соглашаетесь на обработку персональных данных')
    await sleep(5)
    await bot.send_message(user_id, 'Как вас зовут?')
    await bot.set_state(user_id, MyStates.write_name)

@bot.message_handler(commands=['me'])
async def me(message):
    user_id = message.from_user.id
    if check_if_user_filled(user_id):
        await edit_user_info(message)
    else:
        await fill_alert(message)

@bot.message_handler(commands=['help'])
async def help(message):
    user_id = message.from_user.id
    if check_if_user_filled(user_id):
        await bot.send_message(user_id, 'Пожалуйста, опишите с какой технической ошибкой вы столкнулись. Администрация бота постарается обработать ваше обращение как можно скорее! Имеете в виду: фотографии нам не видны, используйте только текст')
        await bot.set_state(user_id, MyStates.write_help)
    else:
        await fill_alert(message)

@bot.callback_query_handler(func=lambda call: True)
async def handle_callback_query(call):
    user_id = call.from_user.id
    if call.data in ['Авто. 1', 'Авто. 0']:
        answer = int(call.data.split('. ')[1])
        add_user_info(user_id, section='with_car', value=answer)
        if check_if_user_filled(user_id):
            await bot.delete_message(user_id, call.message.id)
            await edit_user_info(call.message, user_id=user_id)
        else:
            await bot.edit_message_reply_markup(user_id, call.message.id)
            add_user_info(user_id, section='filled', value=1)
            await bot.send_message(user_id, 'Спасибо за ваш отклик! В скором времени с вами свяжутся. Удачи в вашем нелегком труде и огромная благодарность за то, что не остались в стороне!\n\nПожалуйста, соблюдайте осторожность при работе с мазутом:')
            await bot.send_media_group(user_id, [types.InputMediaPhoto(open(x, 'rb')) for x in ['img/1.jpg','img/2.jpg','img/3.jpg','img/4.jpg','img/5.jpg']])
            await sleep(5)
            await bot.send_message(user_id, 'Для изменения ваших данных введите команду /me')
            sheet_name = select_user_field(user_id, 'wanted_work')
            add_queue(user_id, "add", sheet_name)
    elif call.data in ['Активность. 1', 'Активность. 0']:
        answer = int(call.data.split('. ')[1])
        add_user_info(user_id, section='is_active', value=answer)
        if not answer:
            sheet_name = select_user_field(user_id, 'wanted_work')
            add_queue(user_id, "delete", sheet_name)
        await bot.delete_message(user_id, call.message.id)
        await edit_user_info(call.message, user_id=user_id)
    elif call.data == "Телефон":
        await bot.delete_message(user_id, call.message.id)
        await bot.send_message(user_id, 'Введите ваш телефон:')
        await bot.set_state(user_id, MyStates.write_phone)
    elif call.data == "Район":
        await bot.delete_message(user_id, call.message.id)
        current_value = select_user_field(user_id, 'area') or ''
        selected = current_value.split(", ") if current_value else []
        markup = generate_markup(regions, selected, "Район")
        await bot.send_message(user_id, 'Выберите районы, в которых готовы работать:', reply_markup=markup)
    elif call.data.startswith("Район."):
        _, add_str, idx_str = call.data.split('. ')
        await toggle_item_in_db(user_id, 'area', regions, int(add_str), int(idx_str))
        current_value = select_user_field(user_id, 'area') or ''
        selected = current_value.split(", ") if current_value else []
        markup = generate_markup(regions, selected, "Район")
        await bot.edit_message_text("Выберите районы, в которых готовы работать:", user_id, call.message.id, reply_markup=markup)
        await bot.answer_callback_query(call.id)
    elif call.data == "Район_ok":
        current_value = select_user_field(user_id, 'area')
        if current_value:
            await bot.delete_message(user_id, call.message.id)
            if check_if_user_filled(user_id):
                await edit_user_info(call.message, user_id=user_id)
            else:
                selected = current_value.split(", ") if current_value else []
                markup = generate_markup(work_types, selected, "Работа")
                await bot.send_message(user_id, 'Выберите работу, которую готовы выполнить:', reply_markup=markup)
        else:
            await bot.answer_callback_query(call.id, "Пожалуйста, выберите районы, в которых готовы работать!", show_alert=True)


    elif call.data == "Работа":
        await bot.delete_message(user_id, call.message.id)
        current_value = select_user_field(user_id, 'wanted_work') or ''
        selected = current_value.split(", ") if current_value else []
        markup = generate_markup(work_types, selected, "Работа")
        await bot.send_message(user_id, 'Выберите работу, которую готовы выполнить:', reply_markup=markup)
    elif call.data.startswith("Работа."):
        _, add_str, idx_str = call.data.split('. ')
        await toggle_item_in_db(user_id, 'wanted_work', work_types, int(add_str), int(idx_str))
        current_value = select_user_field(user_id, 'wanted_work') or ''
        selected = current_value.split(", ") if current_value else []
        markup = generate_markup(work_types, selected, "Работа")
        await bot.edit_message_text("Выберите работу, которую готовы выполнить:", user_id, call.message.id, reply_markup=markup)
        await bot.answer_callback_query(call.id)
    elif call.data == "Работа_ok":
        current_value = select_user_field(user_id, 'wanted_work')
        if current_value:
            await bot.delete_message(user_id, call.message.id)
            if check_if_user_filled(user_id):
                await edit_user_info(call.message, user_id=user_id)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text="Да", callback_data="Авто. 1"),
                        types.InlineKeyboardButton(text="Нет", callback_data="Авто. 0"))
                
                await bot.send_message(user_id, 'Есть ли у вас машина?', reply_markup=markup)
                await bot.delete_state(user_id)
        else:
            await bot.answer_callback_query(call.id, "Пожалуйста, выберите работу, которую готовы выполнить!", show_alert=True)
    elif call.data == "Готово":
        await bot.delete_message(user_id, call.message.id)
        await bot.send_message(user_id, 'Спасибо, координаторы штабов свяжутся с вами в ближайшее время!')
        await bot.answer_callback_query(call.id)
    else:
        await bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text'], state=MyStates.write_name)
async def write_phone(message):
    user_id = message.from_user.id
    if message.text == '/me':
        await me(message)
    elif message.text == '/help':
        await help(message)
    else:
        add_user_info(user_id, 'name', message.text)
        if check_if_user_filled(user_id):
            await edit_user_info(message)
        else:
            await bot.send_message(user_id, 'Введите ваш телефон:')
            await bot.set_state(user_id, MyStates.write_phone)

@bot.message_handler(content_types=['text'], state=MyStates.write_phone)
async def write_phone(message):
    user_id = message.from_user.id
    if message.text == '/me':
        await me(message)
    elif message.text == '/help':
        await help(message)
    else:
        is_valid_phone, phone_number = check_phone_number(message.text)
        if is_valid_phone:
            add_user_info(user_id, 'phone', phone_number)
            if check_if_user_filled(user_id):
                await edit_user_info(message)
            else:
                markup = generate_markup(regions, [], "Район")
                await bot.send_message(user_id, "Выберите районы, в которых готовы работать:", reply_markup=markup)
        else:
            await bot.send_message(user_id, "Пожалуйста, введите правильный номер телефона!")


@bot.message_handler(content_types=['text'], state=MyStates.write_help)
async def write_phone(message):
    username, user_id = message.from_user.username, message.from_user.id
    if message.text == '/me':
        await me(message)
    else:
        await operator_bot.send_message(5317048974, f'{user_id} @{username}: {message.text}')
        await bot.send_message(user_id, 'Спасибо, ваше сообщение отправлено администрации бота!')
        await bot.delete_state(user_id)

@bot.message_handler(content_types=['audio','document','video','voice'])
async def incorrect_message(message):
    await bot.send_message(message.from_user.id, 'Я понимаю только текст. Пожалуйста, следуйте инструкциям')

@bot.message_handler(content_types=['text'])
async def write_project_name(message):
    user_id = message.from_user.id
    msg = await bot.send_message(user_id, 'Пожалуйста, используйте кнопки! Если хотите изменить анкету, введите /me')
    await sleep(5)
    await bot.delete_message(user_id, message.id)
    await bot.delete_message(user_id, msg.id)

async def edit_user_info(message, user_id=False):
    if not user_id:
        user_id = message.from_user.id
    username, user_id, name, phone, area, wanted_work, with_car, is_active = select_all_user_data(user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        text="Не ищу работу сейчас  ❌" if is_active else "Готов работать сейчас ✅",
        callback_data="Активность. 0" if is_active else "Активность. 1"))
    markup.add(types.InlineKeyboardButton(text="Телефон", callback_data="Телефон"),
               types.InlineKeyboardButton(text="Район", callback_data="Район"),
               types.InlineKeyboardButton(text="Работа", callback_data="Работа"))
    markup.add(types.InlineKeyboardButton(
        text="Больше нет машины ❌" if with_car else "Машина появилась ✅",
        callback_data="Авто. 0" if with_car else "Авто. 1"))
    markup.add(types.InlineKeyboardButton(text="Готово", callback_data="Готово"))
    await bot.send_message(
        user_id,
        f'Так выглядит ваша анкета волонтера:\n'
        f'{"Готов работать сейчас ✅" if is_active else "Не ищу работу сейчас ❌"}\n'
        f'Имя: {name}\nТелефон: {phone}\nРайон: {area}\nРабота: {wanted_work}\n'
        f'Машина: {"Есть ✅" if with_car else "Нет ❌"}\n\n'
        f'{"Пожалуйста, нажмите на кнопку «Не ищу работу сейчас ❌», если вы уже нашли работу или отправились на отдых!" if is_active else "Сейчас ваша анкета не видна координаторам. Если хотите помочь, нажмите на кнопку «Готов работать сейчас ✅»"}\n'
        f'Изменить анкету?', reply_markup=markup)
    if is_active:
        sheet_name = select_user_field(user_id, 'wanted_work')
        add_queue(user_id, "add", sheet_name)
    await bot.delete_state(user_id)

async def fill_alert(message):
    user_id = message.from_user.id
    msg = await bot.send_message(user_id, 'Пожалуйста, закончите заполнение анкеты!')
    await sleep(5)
    await bot.delete_message(user_id, message.id)
    await bot.delete_message(user_id, msg.id)

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
run(bot.polling(none_stop=True, interval=0))
