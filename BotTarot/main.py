import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import random
import os
from mistralai import Mistral
import requests
import time

API_TOKEN = ''
MISTRAL_API_KEY =''
model = "pixtral-12b-2409"
bot = AsyncTeleBot(API_TOKEN)
CARDS_FOLDER = 'cards'
TAROT_DECK = ["Шут", "Маг", "Верховная Жрица", "Императрица", "Император",
    "Иерофант", "Влюбленные", "Колесница", "Сила", "Отшельник",
    "Колесо Фортуны", "Справедливость", "Повешенный", "Смерть", 
    "Умеренность", "Дьявол", "Башня", "Звезда", "Луна", 
    "Солнце", "Суд", "Мир","Туз Жезлов", "Двойка Жезлов", "Тройка Жезлов", "Четверка Жезлов", 
    "Пятерка Жезлов", "Шестерка Жезлов", "Семерка Жезлов", "Восьмерка Жезлов", 
    "Девятка Жезлов", "Десятка Жезлов", "Паж Жезлов", "Рыцарь Жезлов", 
    "Королева Жезлов", "Король Жезлов","Туз Кубков", "Двойка Кубков", "Тройка Кубков", "Четверка Кубков", 
    "Пятерка Кубков", "Шестерка Кубков", "Семерка Кубков", "Восьмерка Кубков", 
    "Девятка Кубков", "Десятка Кубков", "Паж Кубков", "Рыцарь Кубков", 
    "Королева Кубков", "Король Кубков","Туз Мечей", "Двойка Мечей", "Тройка Мечей", "Четверка Мечей", 
    "Пятерка Мечей", "Шестерка Мечей", "Семерка Мечей", "Восьмерка Мечей", 
    "Девятка Мечей", "Десятка Мечей", "Паж Мечей", "Рыцарь Мечей", 
    "Королева Мечей", "Король Мечей","Туз Пентаклей", "Двойка Пентаклей", "Тройка Пентаклей", "Четверка Пентаклей", 
    "Пятерка Пентаклей", "Шестерка Пентаклей", "Семерка Пентаклей", "Восьмерка Пентаклей", 
    "Девятка Пентаклей", "Десятка Пентаклей", "Паж Пентаклей", "Рыцарь Пентаклей", 
    "Королева Пентаклей", "Король Пентаклей"]
user_histories = {}
user_diaries = {}
user_states = {}

@bot.message_handler(commands=['start'])
async def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    help_item = types.KeyboardButton("Помощь")
    deck_item = types.KeyboardButton("Получить расклад Таро")
    dict_item = types.KeyboardButton("Справочник толкований")
    donate_item = types.KeyboardButton("Донат")
    history_item = types.KeyboardButton("История раскладов")
    diary_item = types.KeyboardButton("Личный дневник")
    diary_view_item = types.KeyboardButton("Просмотр дневника")
    markup.add(deck_item, dict_item, help_item, donate_item, history_item, diary_item, diary_view_item)
    await bot.send_message(message.chat.id, "Привет, я ТароБот!", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    user_id = message.chat.id
    if user_states.get(user_id) == "writing_diary":
        await save_diary_entry(message)
        user_states[user_id] = None
        return
    if message.text == "Помощь":
        await bot.send_message(message.chat.id,
"""
ТароБот разработан для создания и автоматической отправки
раскладов Таро.

Для получения расклада нажмите кнопку 'Получить расклад Таро'.
Для получения информации о толковании карт нажмите кнопку
'Справочник толкований'.
Для просмотра вашей истории раскладов нажмите кнопку 'История раскладов'.
Для записи в личный дневник нажмите кнопку 'Личный дневник'.
Для просмотра записей в личном дневнике нажмите кнопку 'Просмотр дневника'.
"""
)
    elif message.text == "Получить расклад Таро":
        cards = random.sample(TAROT_DECK, 3)
        result_message = (f"Ваш расклад Таро:\n1. Прошлое: {cards[0]}\n"
                          f"2. Настоящее: {cards[1]}\n3. Будущее: {cards[2]}")
        await bot.send_message(message.chat.id, result_message)
        if user_id not in user_histories:
            user_histories[user_id] = []
        user_histories[user_id].append(result_message)
        for card in cards:
            card_path = os.path.join(CARDS_FOLDER, f"{card}.jpg")
            if os.path.exists(card_path):
                with open(card_path, 'rb') as photo:
                    await bot.send_photo(message.chat.id, photo)
            else:
                await bot.send_message(message.chat.id, f"Изображение для карты '{card}' не найдено.")

        print("Вызов интерпретации для карт:", cards)  # Логирование
        interpretation = await get_tarot_interpretation_huggingface(cards)
        await bot.send_message(message.chat.id, f"Интерпретация расклада:\n{interpretation}")
        print("Получена интерпретация:", interpretation)  # Логирование
    elif message.text == "Справочник толкований":
        await bot.send_message(message.chat.id, "https://magya-online.ru/znachenie_kart_taro_koshek")
    elif message.text == "Донат":
        await bot.send_message(message.chat.id,
        "Дорогой мой, помоги цыганке на хлеб насущный и счастье себе привлечёшь! 😊\n"
        "Ты можешь перевести любую сумму по ссылке: https://donate.example.com")
    elif message.text == "История раскладов":
        if user_id in user_histories and user_histories[user_id]:
            history = "\n\n".join(user_histories[user_id])
            await bot.send_message(message.chat.id, f"Вот ваша история раскладов:\n\n{history}")
        else:
            await bot.send_message(message.chat.id, "У вас пока нет сохранённой истории раскладов.")
    elif message.text == "Личный дневник":
        await bot.send_message(message.chat.id, "Напишите запись для личного дневника:")
        user_states[user_id] = "writing_diary"
    elif message.text == "Просмотр дневника":
        if user_id in user_diaries and user_diaries[user_id]:
            diary_entries = "\n\n".join(user_diaries[user_id])
            await bot.send_message(message.chat.id, f"Вот ваши записи в дневнике:\n\n{diary_entries}")
        else:
            await bot.send_message(message.chat.id, "Ваш личный дневник пока пуст.")
    else:
        await bot.send_message(message.chat.id,
    "Такой команды нет. Попробуйте команды из меню")

async def save_diary_entry(message):
    user_id = message.chat.id
    entry = message.text
    if user_id not in user_diaries:
        user_diaries[user_id] = []
    user_diaries[user_id].append(entry)
    await bot.send_message(message.chat.id, "Запись добавлена в ваш личный дневник.")

async def get_tarot_interpretation_huggingface(cards):
    client = Mistral(api_key=MISTRAL_API_KEY)
    chat_response = client.chat.complete(
        model = model,
        messages = [
            {
                "role": "user",
                "content": f"Интерпретируй расклад Таро:\n"
                           f"1. Прошлое: {cards[0]}\n"
                           f"2. Настоящее: {cards[1]}\n"
                           f"3. Будущее: {cards[2]}\n"
                           f"Объясни, что может значить этот расклад.",
            }
        ]
    )
    return chat_response.choices[0].message.content
asyncio.run(bot.polling())
