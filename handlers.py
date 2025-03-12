from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from contacts import contacts

router = Router()

from aiogram import Router, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from contacts import contacts  # Убедись, что импорт правильный

router = Router()

@router.message(F.text.lower() == "/quick_contacts")
async def quick_contacts(message: types.Message):
    print("✅ quick_contacts вызван!")  # Проверяем, вызывается ли обработчик
    buttons = [
        ("• Деканат", "contact_dean"),
        ("• Департамент по Социально-Воспитательной Работе (ДСВР)", "contact_dsvr"),
        ("• Департамент Науки и Инноваций (ДНИ)", "contact_dni"),
        ("• Цифровой институт непрерывного образования (ЦИНО)", "contact_cino"),
        ("• Департамент Информационных Технологий (ДИТ)", "contact_dit"),
        ("• Академический департамент", "contact_academic"),
        ("• Офис регистратора", "contact_registrar"),
        ("• Центр карьеры", "contact_career"),
        ("• Студенческий отдел", "contact_students"),
        ("• Маркетинг", "contact_marketing"),
        ("• Финансовый департамент", "contact_finance"),
        ("• Департамент наук о данных", "contact_data_science"),
        ("• Департамент кибербезопасности", "contact_cybersec"),
        ("• Департамент программной инженерии", "contact_se")
    ]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data)] for text, data in buttons]
    )

    await message.answer("Выберите нужный отдел:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("contact_"))
async def contact_info(callback: CallbackQuery):
    contact = contacts.get(callback.data)

    if contact:
        keyboard = None
        if "callback" in contact:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=contact["button_text"], callback_data=contact["callback"])]
            ])
        await callback.message.answer(contact["text"], reply_markup=keyboard)
        await callback.answer()



