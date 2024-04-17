import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from crafts import crafts

TOKEN = '7150553102:AAGErQj8OVRZBbeJscIOh3m7wD3897z-G1U'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

async def set_default_commands(dp):
    await bot.set_my_commands([
        types.BotCommand('start', 'Запустити бота'),
        types.BotCommand('add_poison', 'Додати новий зілля (для адміна)'),
        types.BotCommand('user_id', "Ваш ID"),
        types.BotCommand('delete_poison', 'Видалити зілля (для адміна)'),
                        ])

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    crafts_choice = InlineKeyboardMarkup()
    for craft in crafts:
        button = InlineKeyboardButton(text=craft, callback_data=craft)
        crafts_choice.add(button)
    await message.answer(text='Привіт! Я - MPCH яке зілля тобі потрібно?', reply_markup=crafts_choice)


@dp.callback_query_handler(lambda callback_query: callback_query.data in crafts.keys())
async def get_potion_info(callback_query: types.CallbackQuery):
    craft_name = callback_query.data
    craft_data = crafts[craft_name]

    await bot.send_photo(callback_query.message.chat.id, craft_data['craft'])

    url = craft_data['site_url']
    description = craft_data['description']
    likes = craft_data.get('likes', 0)
    dislikes = craft_data.get('dislikes', 0)

    message = f"<b>Ссылка на более подробную информацию: </b>{url}\n\n<b>Описание: </b>{description}\n\n<b>Лайки: </b>{likes}\n<b>Дизлаки: </b>{dislikes}"

    buttons = InlineKeyboardMarkup()
    like_button = InlineKeyboardButton(text='❤️', callback_data=f'like_{craft_name}')
    dislike_button = InlineKeyboardButton(text='💔', callback_data=f'dislike_{craft_name}')
    buttons.add(like_button, dislike_button)

    await bot.send_message(callback_query.message.chat.id, message, parse_mode='html', reply_markup=buttons)


voted_users = {}

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith(('like_', 'dislike_')))
async def like_or_dislike(call: types.CallbackQuery):
    action, craft_name = call.data.split('_')[0], '_'.join(call.data.split('_')[1:])
    craft_data = crafts.get(craft_name)

    if not craft_data:
        return

    user_id = call.from_user.id

    if craft_name in voted_users.get(user_id, []):
        return

    likes = craft_data.get('likes', 0)
    dislikes = craft_data.get('dislikes', 0)

    if action == 'like':
        likes += 1
    else:
        dislikes += 1

    craft_data['likes'] = likes
    craft_data['dislikes'] = dislikes

    voted_users.setdefault(user_id, []).append(craft_name)

    await bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )

    await bot.edit_message_text(
        f"<b>Ссылка на более подробную информацию: </b>{craft_data['site_url']}\n\n"
        f"<b>Описание: </b>{craft_data['description']}\n\n"
        f"<b>Лайки: </b>{likes}\n<b>Дизлаки: </b>{dislikes}",
        parse_mode='html',
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=call.message.reply_markup
    )

    
admins = {947523052}
async def add_new_poison(message: types.Message, state: FSMContext):
    await state.set_state('set_poison_name')
    await message.answer(text='Введіть назву зілля, який хочете додати')

@dp.message_handler(commands=['add_poison'])
async def admin_add_poison(message: types.Message):
    if message.from_user.id in admins:
        await add_new_poison(message, dp.current_state(chat=message.chat.id, user=message.from_user.id))
    else:
        await message.answer("У вас нет прав на добавление зелий.")
poison_name = ''


@dp.message_handler(state='set_poison_name')
async def set_poison_name(message: types.Message, state: FSMContext):
    global poison_name
    if len(message.text) > 24:
        message.answer = 'Назва зілля повинна бути менше 24 символів'
    else:
        poison_name = message.text
        crafts[poison_name] = {}
        await state.set_state('set_site_url')
        await message.answer(text='Введіть посилання на сайт зілля')


@dp.message_handler(state='set_site_url')
async def set_site_url(message: types.Message, state: FSMContext):
    global poison_name
    url = message.text
    crafts[poison_name]['site_url'] = url
    await state.set_state('set_description')
    await message.answer(text='Введіть опис зілля')


@dp.message_handler(state='set_description')
async def set_description(message: types.Message, state: FSMContext):
    global poison_name
    description = message.text
    crafts[poison_name]['description'] = description
    await state.set_state('set_craft')
    await message.answer(text='Введіть посилання крафт на зілля')

@dp.message_handler(state='set_craft')
async def set_craft(message: types.Message, state: FSMContext):
    global poison_name
    craft_url = message.text
    crafts[poison_name]['craft'] = craft_url
    await state.reset_state()
    await message.answer(text='Зелье успешно добавлено!')

@dp.message_handler(commands=['user_id'])
async def user_id(message: types.Message):
    await message.answer(message.from_user.id)



@dp.message_handler(commands=['delete_poison'])
async def delete_poison(message: types.Message):
    if message.from_user.id in admins:
        await message.answer("Введите название зелья, которое хотите удалить:")
        dp.register_message_handler(delete_poison_confirm, state='*')
    else:
        await message.answer("У вас нет прав на удаление зелий.")

async def delete_poison_confirm(message: types.Message, state: FSMContext):
    poison_name = message.text
    if poison_name in crafts:
        del crafts[poison_name]
        await message.answer(f"Зелье '{poison_name}' успешно удалено.")
    else:
        await message.answer("Такого зелья не существует.")
    await state.finish()





async def on_startup(dp):
    await set_default_commands(dp)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)


