from PIL import Image
import opennsfw2 as n2
import numpy as np
import json
import pickledb
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils.exceptions import Throttled
from aiogram.utils import executor
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonPollType,
    ReplyKeyboardMarkup,
)

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from myconfig import *  # <--

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
# for db
# nsfw
##########################
start_pressed = pickledb.load('start_pressed.db', False)
usersID = pickledb.load('usersID.db', False)


state_photo = {}   # для фото
state_caption = {}   # для фото
locationn = {}   # для location
language = {}   # для localisation
# Define dictionary to keep track of likes and dislikes for each message
message_ratings = {}
# Define dictionary to keep track of user IDs who have already rated each message
user_ratings = {}
send_to_all = {}  # to send information to all users in bot

# id стикерa (@idsticker_bot)
loading_sti = 'CAACAgIAAxkBAAEItPNkRp2n4RlDpujrFbbn1PIuRZ-WtgACDgADr8ZRGrdbgux-ASf3LwQ'
main_channel_ID = '-1001906709886'  # ID канала в с новостями
channel_NSFW = '-1001549102620'  # ID канала   с NTFS
channel_history = '-1001920856759'  # ID канала   с History

supported_languages = ['en', 'ru', 'uk']
#################


class UserState(StatesGroup):
    photo = State()
    location = State()
    caption = State()
    # for sending to all members
    text_for_sending = State()
    sending = State()
    text_for_admin = State()
    sending_admin = State()
#################


#################
# Load the localized messages from the JSON file
with open("messages.json", "r", encoding="utf-8") as f:
    messages = json.load(f)
#################

#################


async def anti_flood(*args, **kwargs):
    m = args[0]
    do_not_flood_text = messages["do_not_flood_text"][language[m.from_user.id]]
    await m.answer(do_not_flood_text, parse_mode='html')
#################

#################


@dp.message_handler(commands=['sendlistwithusersqqq'])
async def command(message):
    with open('start_pressed.db', 'r') as handle:
        parsed = json.load(handle)

    f = open("start_pressed.csv", "w")
    for s in parsed:
        f.write(s + "," + parsed[s] + "\n")
    f.close()

    doc = open('start_pressed.csv', 'rb')
    start_pressed_db = open('start_pressed.db', 'rb')
    await bot.send_document(chat_id=message.chat.id, document=doc)
    await bot.send_document(chat_id=message.chat.id, document=start_pressed_db)
#################

#################


@dp.message_handler(commands=['whosentphotos'])
async def command(message):
    with open('usersID.db', 'r') as handle:
        parsed = json.load(handle)

    f = open("usersID.csv", "w")
    for s in parsed:
        f.write(s + "," + parsed[s] + "\n")
    f.close()

    doc = open('usersID.csv', 'rb')
    usersID_db = open('usersID.db', 'rb')
    await bot.send_document(chat_id=message.chat.id, document=doc)
    await bot.send_document(chat_id=message.chat.id, document=usersID_db)
#################

#################


@dp.message_handler(commands=['sendallfromadminqqq'])
async def question(message: types.Message, state: FSMContext):
    await message.answer('Введи текст который нужно отправить всем')
    await UserState.text_for_sending.set()


@dp.message_handler(content_types=['text'], state=UserState.text_for_sending)
async def send_to_channels(message: types.Message, state: FSMContext):
    await state.update_data(text_for_sending=message.text)
    rmk = ReplyKeyboardMarkup(
        row_width=2, one_time_keyboard=True, resize_keyboard=True)
    rmk.add(InlineKeyboardButton("Да ✅"), InlineKeyboardButton("❌ cancel"))
    await message.answer('Отправить данное сообщение всем кто подписан на бота?', reply_markup=rmk)
    await UserState.sending.set()


@dp.message_handler(content_types=['text'], state=UserState.sending)
async def get_card(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == 'Да ✅':
        print(start_pressed.getall())
        for i in start_pressed.getall():
            await bot.send_message(i, data['text_for_sending'], disable_notification=True)
        await state.finish()
    else:
        await message.answer('Отправка отменена')
        await state.finish()
#################

################# что умее этот бот	#################


@dp.message_handler(commands=['start'])  # какие команды отслеживаем
@dp.throttled(anti_flood, rate=60)
async def start(message):
    if message.from_user.language_code not in supported_languages:
        language[message.from_user.id] = 'en'
    else:
        language[message.from_user.id] = message.from_user.language_code
    send_photo_request = messages["send_photo"][language[message.from_user.id]]
    await message.answer(f"{send_photo_request}", parse_mode='html')
    start_pressed.set(str(f'{message.from_user.id}'), str(
        f'@{message.from_user.username} | {message.from_user.first_name} {message.from_user.last_name}'))
    start_pressed.dump()
#################


#######################################################################################################################
# Define callback function for like button
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('like'))
async def process_callback_like(callback_query: types.CallbackQuery):
    message_id = callback_query.message.message_id
    user_id = callback_query.from_user.id
    if message_id not in message_ratings:
        message_ratings[message_id] = {'likes': 0, 'dislikes': 0}
    if message_id not in user_ratings:
        user_ratings[message_id] = set()
    if 'dislike' in user_ratings[message_id]:
        message_ratings[message_id]['dislikes'] -= 1
        user_ratings[message_id].remove('dislike')
    if user_id in user_ratings[message_id]:
        if message_ratings[message_id]['likes'] == 0:
            await bot.answer_callback_query(callback_query.id, text="You cannot remove your like, it's already 0.")
        else:
            message_ratings[message_id]['likes'] -= 1
            user_ratings[message_id].remove(user_id)
            await bot.answer_callback_query(callback_query.id, text="You removed your like!")
    else:
        message_ratings[message_id]['likes'] += 1
        user_ratings[message_id].add(user_id)
        await bot.answer_callback_query(callback_query.id, text="You liked this message!")
    print(callback_query)
    await update_message_rating(callback_query.message, callback_query.data[5:])

# Define callback function for dislike button


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('dislike'))
async def process_callback_dislike(callback_query: types.CallbackQuery):
    message_id = callback_query.message.message_id
    user_id = callback_query.from_user.id
    if message_id not in message_ratings:
        message_ratings[message_id] = {'likes': 0, 'dislikes': 0}
    if message_id not in user_ratings:
        user_ratings[message_id] = set()
    if 'like' in user_ratings[message_id]:
        message_ratings[message_id]['likes'] -= 1
        user_ratings[message_id].remove('like')
    if user_id in user_ratings[message_id]:
        if message_ratings[message_id]['dislikes'] == 0:
            await bot.answer_callback_query(callback_query.id, text="You cannot remove your dislike, it's already 0.")
        else:
            message_ratings[message_id]['dislikes'] -= 1
            user_ratings[message_id].remove(user_id)
            await bot.answer_callback_query(callback_query.id, text="You removed your dislike!")
    else:
        message_ratings[message_id]['dislikes'] += 1
        user_ratings[message_id].add(user_id)
        await bot.answer_callback_query(callback_query.id, text="You disliked this message!")
    await update_message_rating(callback_query.message, callback_query.data[8:])
#######################################################################################################################

####


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals=['❌ Cancel', '❌ Отмена'], ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    operation_canceled_text = messages["operation_canceled_text"][language[message.from_user.id]]
    if current_state is None:
        return
    await state.finish()
    await message.reply(operation_canceled_text)


@dp.message_handler(content_types=['photo'])
@dp.throttled(anti_flood, rate=60)
async def get_photo(message: types.Message, state: FSMContext):
    # usersID.set(str(f'{message.from_user.id}'), str(f'@{message.from_user.username}'))
    # usersID.dump()
    # with open('loading.tgs', 'rb') as sticker_file: # https://chpic.su/en/emojis/LoadingEmoji/067/
    # msg = await bot.send_animation(message.chat.id, animation=sticker_file)
    if message.from_user.language_code not in supported_languages:
        language[message.from_user.id] = 'en'
    else:
        language[message.from_user.id] = message.from_user.language_code
    button_cancel = messages["button_cancel"][language[message.from_user.id]]
    share_location_button = messages["share_location_button"][language[message.from_user.id]]
    operation_canceled = messages["operation_canceled"][language[message.from_user.id]]
    plese_send_your_location = messages["plese_send_your_location"][language[message.from_user.id]]
    try:
        file_info = await bot.get_file(message.photo[-1].file_id)
        state_photo[message.from_user.id] = await bot.download_file(file_info.file_path)
        rmk = ReplyKeyboardMarkup(
            row_width=2, one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton(f"❌ {button_cancel}"),
                KeyboardButton(f"{share_location_button} 📍", request_location=True))
        await message.answer(f"{plese_send_your_location} 📍", reply_markup=rmk)
        await state.update_data(photo=state_photo[message.from_user.id])
        await UserState.photo.set()
    except Exception:
        await state.finish()
        await message.reply('operation_canceled')


@dp.message_handler(content_types=['location'], state=UserState.photo)
async def get_location(message: types.Message, state: FSMContext):
    button_cancel = messages["button_cancel"][language[message.from_user.id]]
    button_skip = messages["button_skip"][language[message.from_user.id]]
    caption_text_request = messages["caption_text_request"][language[message.from_user.id]]
    you_can_skip_caption = messages["you_can_skip_caption"][language[message.from_user.id]]
    if message.location is not None:
        latitude = message.location.latitude
        longitude = message.location.longitude
        await state.update_data(location=f"https://www.google.com/maps/place/{latitude},{longitude}")
        await UserState.location.set()
        rmk = ReplyKeyboardMarkup(
            row_width=2, one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton(f"❌ {button_cancel}"),
                KeyboardButton(button_skip))
        await message.answer(f"{caption_text_request}\n\n<i>*{you_can_skip_caption}</i>", parse_mode='html', reply_markup=rmk)

    else:
        location_button = KeyboardButton(
            text="share_location_button", request_location=True)
        markup = ReplyKeyboardMarkup(
            keyboard=[[location_button]], one_time_keyboard=True, resize_keyboard=True)
        await message.answer("plese_send_your_location", reply_markup=markup)


@dp.message_handler(content_types=['text'], state=UserState.location)
async def get_text(message: types.Message, state: FSMContext):
    button_skip = messages["button_skip"][language[message.from_user.id]]
    state_caption[message.from_user.id] = message.text
    data = await state.get_data()
    if state_caption[message.from_user.id] == button_skip:
        message_id = message.message_id
        if message_id not in message_ratings:
            message_ratings[message_id] = {'likes': 0, 'dislikes': 0}
        if message_id not in user_ratings:
            user_ratings[message_id] = set()
        markup = InlineKeyboardMarkup(row_width=2)
        b1 = InlineKeyboardButton("View on map 🗺", url=f"{data['location']}")
        b2 = InlineKeyboardButton(
            "👍 " + str(message_ratings[message_id]['likes']), callback_data=f"like,{data['location']}")
        b3 = InlineKeyboardButton(
            "👎 " + str(message_ratings[message_id]['dislikes']), callback_data=f"dislike,{data['location']}")
        markup.add(b2, b3, b1)
        data['photo'].seek(0)
        # await bot.send_photo(channel_NSFW, data['photo'], parse_mode='html', reply_markup=markup)# change to main channel
        # await message.answer("Thanks, Your photo posted")
        usersID_counter = usersID.get(
            str(f'@{message.from_user.username} {message.from_user.id}'))
        if usersID_counter == False:
            usersID.set(
                str(f'@{message.from_user.username} {message.from_user.id}'), '1')
        else:
            usersID.set(str(
                f'@{message.from_user.username} {message.from_user.id}'), str(int(usersID_counter) + 1))
        usersID.dump()
        we_will_let_you_know = messages["we_will_let_you_know"][language[message.from_user.id]]
        await message.answer(we_will_let_you_know)
        try:
            # nsfw
            image_path = data['photo']
            pil_image = Image.open(image_path)
            image = n2.preprocess_image(pil_image, n2.Preprocessing.YAHOO)
            model = n2.make_open_nsfw_model()
            inputs = np.expand_dims(image, axis=0)
            predictions = model.predict(inputs)
            sfw_probability, nsfw_probability = predictions[0]
            print(sfw_probability, nsfw_probability)
            print(f"@{message.from_user.username} | {message.from_user.id}")
            if nsfw_probability > 0.3:
                raise Exception()
            ###
            data = await state.get_data()
            data['photo'].seek(0)
            # change to main channel
            # change to main channel
            await bot.send_photo(channel_NSFW, data['photo'], parse_mode='html', reply_markup=markup)
            thanks_photo_posted = messages["thanks_photo_posted"][language[message.from_user.id]]
            await message.answer(thanks_photo_posted)
            # дублируем в channel_history
            data = await state.get_data()
            data['photo'].seek(0)
            await bot.send_photo(channel_history, data['photo'], caption=f"@{message.from_user.username} {message.from_user.id}")
            await state.finish()
        except Exception:
            data = await state.get_data()
            data['photo'].seek(0)
            await bot.send_photo(channel_NSFW, data['photo'], caption=f"""Прислал: @{message.from_user.username} | {message.from_user.id} | {message.from_user.first_name} {message.from_user.last_name}\n\n {nsfw_probability}""")
            NSFW_not_posted = messages["NSFW_not_posted"][language[message.from_user.id]]
            await message.answer(f"{NSFW_not_posted}")
            await state.finish()

    else:
        while len(message.text.split()) >= 50:
            text_is_too_large = messages["text_is_too_large"][language[message.from_user.id]]
            await message.answer(text_is_too_large)
            message = await bot.wait_for("message", check=lambda m: m.from_user.id == message.from_user.id and len(m.text.split()) < 50)

        state_caption[message.from_user.id] = message.text
        await state.update_data(caption=f"{state_caption[message.from_user.id]}")
        await UserState.caption.set()
        data = await state.get_data()
        message_id = message.message_id
        if message_id not in message_ratings:
            message_ratings[message_id] = {'likes': 0, 'dislikes': 0}
        if message_id not in user_ratings:
            user_ratings[message_id] = set()

        markup = InlineKeyboardMarkup(row_width=2)
        b1 = InlineKeyboardButton("View on map 🗺", url=f"{data['location']}")
        b2 = InlineKeyboardButton(
            "👍 " + str(message_ratings[message_id]['likes']), callback_data=f"like,{data['location']}")
        b3 = InlineKeyboardButton(
            "👎 " + str(message_ratings[message_id]['dislikes']), callback_data=f"dislike,{data['location']}")
        markup.add(b2, b3, b1)
        data['photo'].seek(0)
        usersID_counter = usersID.get(
            str(f'@{message.from_user.username} {message.from_user.id}'))
        if usersID_counter == False:
            usersID.set(
                str(f'@{message.from_user.username} {message.from_user.id}'), '1')
        else:
            usersID.set(str(
                f'@{message.from_user.username} {message.from_user.id}'), str(int(usersID_counter) + 1))
        usersID.dump()
        we_will_let_you_know = messages["we_will_let_you_know"][language[message.from_user.id]]
        await message.answer(we_will_let_you_know)

        try:
            # nsfw
            image_path = data['photo']
            pil_image = Image.open(image_path)
            image = n2.preprocess_image(pil_image, n2.Preprocessing.YAHOO)
            model = n2.make_open_nsfw_model()
            inputs = np.expand_dims(image, axis=0)
            predictions = model.predict(inputs)
            sfw_probability, nsfw_probability = predictions[0]
            print(sfw_probability, nsfw_probability)
            print(f"@{message.from_user.username} | {message.from_user.id}")
            if nsfw_probability > 0.3:
                raise Exception()
            ###
            data = await state.get_data()
            data['photo'].seek(0)
            # change to main channel
            await bot.send_photo(channel_NSFW, data['photo'], caption=f"{state_caption[message.from_user.id]}", parse_mode='html', reply_markup=markup)
            thanks_photo_posted = messages["thanks_photo_posted"][language[message.from_user.id]]
            await message.answer(thanks_photo_posted)
            # дублируем в channel_history
            data = await state.get_data()
            data['photo'].seek(0)
            await bot.send_photo(channel_history, data['photo'], caption=f"@{message.from_user.username} {message.from_user.id}")
            await state.finish()
        except Exception:
            data = await state.get_data()
            data['photo'].seek(0)
            await bot.send_photo(channel_NSFW, data['photo'], caption=f"""Прислал: @{message.from_user.username} | {message.from_user.id} | {message.from_user.first_name} {message.from_user.last_name}\n\n {nsfw_probability}""")
            NSFW_not_posted = messages["NSFW_not_posted"][language[message.from_user.id]]
            await message.answer(f"{NSFW_not_posted}")
            await state.finish()
        # дублируем в channel_history


# Define function to update the message rating with new like/dislike counts
async def update_message_rating(message: types.Message, id):
    message_id = message.message_id
    if message_id not in message_ratings:
        return
    rating = message_ratings[message_id]
    # data = await UserState.photo.get_data()
    b1 = InlineKeyboardButton("View on map 🗺", url=id)
    like_button = InlineKeyboardButton(
        "👍 " + str(rating['likes']), callback_data=f'like,{id}')
    dislike_button = InlineKeyboardButton(
        "👎 " + str(rating['dislikes']), callback_data=f'dislike,{id}')
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(like_button, dislike_button, b1)
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=markup)

##################


@dp.message_handler(text_contains=['I have a question'])
@dp.throttled(anti_flood, rate=60)
async def question(message: types.Message, state: FSMContext):
    enter_text_to_admin = messages["enter_text_to_admin"][language[message.from_user.id]]
    await message.answer(enter_text_to_admin)
    await UserState.text_for_admin.set()


@dp.message_handler(content_types=['text'], state=UserState.text_for_admin)
async def send_to_channels(message: types.Message, state: FSMContext):
    await state.update_data(text_for_admin=message.text)
    rmk = ReplyKeyboardMarkup(
        row_width=2, one_time_keyboard=True, resize_keyboard=True)
    rmk.add(InlineKeyboardButton("Yes ✅"), InlineKeyboardButton("❌ cancel"))
    await message.answer('Send this message to admin?', reply_markup=rmk)
    await UserState.sending_admin.set()


@dp.message_handler(content_types=['text'], state=UserState.sending_admin)
async def get_card(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == 'Yes ✅':
        await bot.send_message(651726581, f"From @{message.from_user.username} {message.from_user.id} \n {data['text_for_admin']}")
        thanks_admin_will_answer = messages["thanks_admin_will_answer"][language[message.from_user.id]]
        await message.answer(thanks_admin_will_answer)
        await state.finish()
    else:
        operation_canceled_text = messages["operation_canceled_text"][language[message.from_user.id]]
        await message.answer(operation_canceled_text)
        await state.finish()
#################


@dp.message_handler(commands=['qqq'])
async def qqq(message):
    markup = types.InlineKeyboardMarkup()
    b1 = types.InlineKeyboardButton(
        "👉 Send photo 👈", url="https://t.me/found_it_outside_bot")
    markup.add(b1)
    await bot.send_message(main_channel_ID, """Hi there 👋
    \nWelcome to our channel! Here, you can share your <u>photos</u> and <u>location</u> of <i>places</i>, <i>things</i>, and more, to inspire others to explore and discover new wonders of the world 🌎.
    \nUse button below and send you first photo 👇
	\nif You have <b>questions</b> or <b>suggestions</b> just type in <b>bot</b>:
	 <code>I have a question</code>""", parse_mode='html', reply_markup=markup)


if __name__ == '__main__':
    executor.start_polling(dp)
