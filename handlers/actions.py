import asyncio
from dispatcher import bot
from aiogram import types
from main import BotDB, dp
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
import aiogram.utils.markdown as md
from datetime import datetime, timedelta


# ===================================== Классы состояний для последовательного заполнения ==============================
# создаём форму и указываем поля
class RemOnDate(StatesGroup):
    date = State()
    time = State()
    msg = State()


class RemOnTime(StatesGroup):
    time = State()
    msg = State()


# keyboards.py
inline_btn_1 = InlineKeyboardButton('Напоминание на дату', callback_data='RemOnDate')
inline_btn_2 = InlineKeyboardButton('Ежедневное напоминание', callback_data='RemOnTime')
inline_btn_3 = InlineKeyboardButton('Сегодня', callback_data='Today')
inline_btn_4 = InlineKeyboardButton('Завтра', callback_data='Tomorrow')
inline_btns = InlineKeyboardMarkup().add(inline_btn_1).add(inline_btn_2)


button_hi = KeyboardButton('Привет! 👋')
greet_kb1 = ReplyKeyboardMarkup(resize_keyboard=True).add(button_hi)


async def on_startup(x):
    asyncio.create_task(check_reminders())


# Функция наачала взаимодействия с ботом.
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not BotDB.user_exists(message.from_user.id):
        BotDB.add_user(message.from_user.id)

    await message.bot.send_message(message.from_user.id,
                                   "Добро пожаловать!\n"
                                   "Данный бот позволяет создать напоминание для события с "
                                   "точностью до минуты. Следуйте подсказкам бота, чтобы сделать это.\n"
                                   "Напишите /help, чтобы получить справку.",
                                   reply_markup=inline_btns)


@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/help` command
    """
    await message.reply(md.text(md.text(md.bold('Reminder Bot\n')),
                                md.text('Данный бот позволяет создавать напоминания с точностью до минуты.\n'
                                        'Сейчас доступны следующие варианты уведомлений:'),
                                md.text('1. Напоминание на определенную дату и время.'),
                                md.text('2. Ежедневное напоминание в определенное время.\n'),
                                md.text('После установки напоминания, когда подойдет нужное время и дата, '
                                        'бот пришлет уведомление.\n'),
                                md.text('Для напоминания устанавливается дата и время, или только время, '
                                        'а также его название.'),
                                sep='\n',
                                ),
                        parse_mode=ParseMode.MARKDOWN)


# ===================================== Установка напоминаний ==========================================================
@dp.message_handler(commands=['r', 'remind'])
@dp.message_handler(Text(equals='напомнить', ignore_case=True), state='*')
async def reminder_handler(message: types.Message):
    await message.reply("Установить напоминание", reply_markup=inline_btns)


# Добавляем возможность отмены, если пользователь передумал заполнять
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('Установка напоминания отменена')


# ===================================== Показать активные напоминания ==================================================
@dp.message_handler(commands=['h'])
async def send_welcome(message: types.Message):
    reminds = BotDB.get_records(BotDB.get_user_id(message.from_user.id))
    print(reminds)
    ans = ''
    for r in reminds:
        ans += f'Напоминание - {r[4]}\n'
        if r[2]:
            ans += 'Ежедневное\n'
            ans += f'Время напоминания - {datetime.strptime(r[3], "%Y-%m-%d %H:%M:%S").time().isoformat()}'
        else:
            ans += 'Однократное\n'
            ans += f'Дата напоминания - {datetime.strptime(r[3], "%Y-%m-%d %H:%M:%S").date().isoformat()}\n'
            ans += f'Время напоминания - {datetime.strptime(r[3], "%Y-%m-%d %H:%M:%S").time().isoformat()}'

        ans += '\n \n \n'

    await message.reply(ans)


# ===================================== Установка ежедневного напоминания ==============================================
# Обработка установки напоминания на время
@dp.callback_query_handler(lambda c: c.data == 'RemOnTime')
async def process_callback_remontime(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await RemOnTime.time.set()
    await bot.send_message(callback_query.from_user.id, 'Введите время напоминания\n'
                                                        'Формат: чч:мм (10:00)')


# Сюда приходит ответ с временем
@dp.message_handler(state=RemOnTime.time)
async def process_time_remontime(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # print(datetime.strptime(str(datetime.now().date().isoformat()) + " " + message.text, '%Y-%m-%d %H:%M'))
        data['time'] = datetime.strptime(str(datetime.now().date().isoformat()) + " " + message.text, '%Y-%m-%d %H:%M')

    await RemOnTime.next()
    await message.reply("Укажите название для напоминания")


# Сюда приходит ответ с названием
@dp.message_handler(state=RemOnTime.msg)
async def process_msg_remontime(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['msg'] = message.text
        BotDB.add_record(message.from_user.id, True, str(data['time']), message.text)
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text(f'Установлено ежедневное напоминание - {md.bold(data["msg"])}'),
                md.text(f'Время - {md.bold(data["time"].hour)}:{md.bold(data["time"].minute)}'),
                sep='\n',
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    await state.finish()


# ===================================== Установка напоминания на дату ==================================================
# Обработка установки напоминания на дату
@dp.callback_query_handler(lambda c: c.data == 'RemOnDate')
async def process_callback_remondate(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await RemOnDate.date.set()
    await bot.send_message(callback_query.from_user.id, 'Выберите или введите дату для напоминания',
                           reply_markup=InlineKeyboardMarkup().add(inline_btn_3).add(inline_btn_4))


@dp.callback_query_handler(lambda c: c.data == 'Today', state=RemOnDate.date)
async def process_date_today_remondate(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['date'] = datetime.now()
    await RemOnDate.next()
    await bot.send_message(callback_query.from_user.id,
                           f'Дата напоминаия - {data["date"].date().isoformat()} (сегодня)\n'
                           f'Введите время напоминания\n'
                           f'Формат: чч:мм (10:00)')


@dp.callback_query_handler(lambda c: c.data == 'Tomorrow', state=RemOnDate.date)
async def process_date_tomorrow_remondate(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data['date'] = (datetime.now() + timedelta(days=1))
    await RemOnDate.next()
    await bot.send_message(callback_query.from_user.id,
                           f'Дата напоминаия - {data["date"].date().isoformat()} (завтра)\n'
                           f'Введите время напоминания\n'
                           f'Формат: чч:мм (10:00)')


# Сюда приходит ответ с датой
@dp.message_handler(state=RemOnDate.date)
async def process_date_remondate(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = datetime.strptime(message.text + "." + str(datetime.now().year), '%d.%m.%Y')
        # print(data['date'])
    await RemOnDate.next()
    await bot.send_message(message.chat.id, f'Дата напоминаия - {data["date"].date()}\n'
                                            f'Введите время напоминания\n'
                                            f'Формат: чч:мм (10:00)')


# Сюда приходит ответ с временем
@dp.message_handler(state=RemOnDate.time)
async def process_time_remondate(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = datetime.strptime(str(data['date'].date()) + " " + message.text, '%Y-%m-%d %H:%M')

    await RemOnDate.next()
    await message.reply("Укажите название для напоминания")

# Сюда приходит ответ с названием
@dp.message_handler(state=RemOnDate.msg)
async def process_msg_remondate(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['msg'] = message.text
        BotDB.add_record(message.from_user.id, False, str(data['time']), message.text)
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text(f'Установлено напоминание - {md.bold(data["msg"])}'),
                md.text(f'Дата - {md.bold(data["time"].day)}.{md.bold(data["time"].month)}'),
                md.text(f'Время - {md.bold(data["time"].hour)}:{md.bold(data["time"].minute)}'),
                sep='\n',
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    await state.finish()


# ===================================== Цикл на проверку актуальных уведомлений ========================================
async def check_reminders():
    while True:
        for id in BotDB.get_users():

            for rec in BotDB.get_records(id[0]):
                now = datetime.now()
                if int(rec[2]):
                    if datetime.strptime(rec[3], '%Y-%m-%d %H:%M:%S').hour == now.hour and \
                            datetime.strptime(rec[3], '%Y-%m-%d %H:%M:%S').minute == now.minute:
                        await bot.send_message(id[1], f'Уведомление!\n'
                                                      f'{rec[4]}')
                else:
                    if datetime.strptime(rec[3], '%Y-%m-%d %H:%M:%S').date() == now.date() and \
                            datetime.strptime(rec[3], '%Y-%m-%d %H:%M:%S').hour == now.hour and \
                            datetime.strptime(rec[3], '%Y-%m-%d %H:%M:%S').minute == now.minute:
                        await bot.send_message(id[1], f'Уведомление!\n'
                                                      f'{rec[4]}')
                        BotDB.remove_record(rec[0])

        await asyncio.sleep(60)
