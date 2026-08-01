import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import BOT_TOKEN, ADMIN_ID, STYLES_DIR, STARS_PER_IMAGE, MIN_DEPOSIT
from database import (
    init_db, add_style, get_user_styles, get_style_by_id,
    get_balance, add_balance, deduct_balance,
    add_deposit_record, get_user_deposits
)
from utils.style_analyzer import analyze_style
from utils.image_generator import generate_images

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    waiting_style_name = State()
    waiting_character = State()
    waiting_num_images = State()
    waiting_style_choice = State()
    waiting_deposit_amount = State()

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎨 Generate")
    builder.button(text="➕ Add Style")
    builder.button(text="📋 My Styles")
    builder.button(text="💰 Balance")
    builder.button(text="⭐ Deposit")
    builder.button(text="📜 My Deposits")
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    balance = await get_balance(message.from_user.id)
    text = (
        "Welcome to **StyleForge Bot** 🎨\n\n"
        "Generate high-quality images using your custom art styles.\n\n"
        f"Price: **{STARS_PER_IMAGE} Stars** per image\n"
        f"Your balance: **{balance} ⭐**\n"
        "Admin: Free forever\n\n"
        "Use the buttons below."
    )
    await message.answer(text, reply_markup=main_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "**How to use:**\n\n"
        "1. Add Style → send reference image\n"
        "2. Deposit Stars (min 10)\n"
        "3. Generate → choose style → character → number of images\n"
        "4. Stars will be deducted from your balance\n\n"
        "Admin is always free."
    )

@dp.message(F.text == "💰 Balance")
@dp.message(Command("balance"))
async def show_balance(message: Message):
    balance = await get_balance(message.from_user.id)
    await message.answer(f"💰 Your current balance: **{balance} ⭐**")

@dp.message(F.text == "📜 My Deposits")
@dp.message(Command("deposits"))
async def show_deposits(message: Message):
    deposits = await get_user_deposits(message.from_user.id)
    if not deposits:
        await message.answer("No deposits yet.")
        return
    
    text = "📜 **Your Deposit History:**\n\n"
    for amount, created_at in deposits:
        date = created_at[:16].replace("T", " ")
        text += f"• +{amount} ⭐ — {date}\n"
    
    await message.answer(text)

@dp.message(F.text == "⭐ Deposit")
@dp.message(Command("deposit"))
async def deposit_cmd(message: Message, state: FSMContext):
    await message.answer(
        f"⭐ Enter the amount of Stars you want to deposit\n"
        f"(Minimum: {MIN_DEPOSIT} Stars)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.waiting_deposit_amount)

@dp.message(Form.waiting_deposit_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < MIN_DEPOSIT:
            await message.answer(f"Minimum deposit is {MIN_DEPOSIT} Stars. Try again:")
            return
        if amount > 100000:
            await message.answer("Maximum is 100000 Stars.")
            return
    except:
        await message.answer("Please enter a valid number:")
        return

    prices = [LabeledPrice(label=f"Deposit {amount} Stars", amount=amount)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="StyleForge Deposit",
        description=f"Add {amount} Stars to your wallet",
        payload=f"deposit_{amount}",
        provider_token="",
        currency="XTR",
        prices=prices
    )
    await message.answer(
        f"Please pay **{amount} ⭐** to complete the deposit.",
        reply_markup=main_keyboard()
    )
    await state.clear()

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if payload.startswith("deposit_"):
        amount = int(payload.split("_")[1])
        await add_balance(message.from_user.id, amount)
        await add_deposit_record(message.from_user.id, amount)
        new_balance = await get_balance(message.from_user.id)
        await message.answer(
            f"✅ Payment successful!\n"
            f"+{amount} ⭐ added to your wallet.\n"
            f"New balance: **{new_balance} ⭐**"
        )
    else:
        await message.answer("Payment received.")

@dp.message(F.text == "➕ Add Style")
@dp.message(Command("add_style"))
async def add_style_cmd(message: Message, state: FSMContext):
    await message.answer("Please send me the style reference image now:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_style_name)

@dp.message(Form.waiting_style_name, F.photo)
async def process_style_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = os.path.join(STYLES_DIR, f"{message.from_user.id}_{photo.file_id}.jpg")
    await bot.download_file(file.file_path, file_path)
    await state.update_data(image_path=file_path)
    await message.answer("Image received. Now send a name for this style:")

@dp.message(Form.waiting_style_name, F.text)
async def process_style_name(message: Message, state: FSMContext):
    data = await state.get_data()
    image_path = data.get("image_path")
    if not image_path:
        await message.answer("Error. Try again.", reply_markup=main_keyboard())
        await state.clear()
        return

    name = message.text.strip()
    description = await analyze_style(image_path)
    await add_style(message.from_user.id, name, image_path, description)
    await message.answer(f"✅ Style saved as: **{name}**", reply_markup=main_keyboard())
    await state.clear()

@dp.message(F.text == "📋 My Styles")
@dp.message(Command("list_styles"))
async def list_styles(message: Message):
    styles = await get_user_styles(message.from_user.id)
    if not styles:
        await message.answer("No styles yet. Use Add Style first.")
        return
    text = "Your saved styles:\n\n"
    for s in styles:
        text += f"ID: {s[0]} | {s[1]}\n"
    await message.answer(text)

@dp.message(F.text == "🎨 Generate")
@dp.message(Command("generate"))
async def generate_cmd(message: Message, state: FSMContext):
    styles = await get_user_styles(message.from_user.id)
    if not styles:
        await message.answer("No styles found. Add a style first.")
        return

    builder = InlineKeyboardBuilder()
    for s in styles:
        builder.button(text=f"{s[1]} (ID: {s[0]})", callback_data=f"style_{s[0]}")
    builder.adjust(1)
    await message.answer("Select a style:", reply_markup=builder.as_markup())
    await state.set_state(Form.waiting_style_choice)

@dp.callback_query(F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext):
    style_id = int(callback.data.split("_")[1])
    await state.update_data(style_id=style_id)
    await callback.message.answer("Enter the character name:")
    await state.set_state(Form.waiting_character)
    await callback.answer()

@dp.message(Form.waiting_character)
async def process_character(message: Message, state: FSMContext):
    await state.update_data(character=message.text.strip())
    await message.answer("How many images? (1-10):")
    await state.set_state(Form.waiting_num_images)

@dp.message(Form.waiting_num_images)
async def process_num_images(message: Message, state: FSMContext):
    try:
        num = int(message.text.strip())
        if num < 1 or num > 10:
            await message.answer("Enter a number between 1 and 10")
            return
    except:
        await message.answer("Enter a valid number")
        return

    data = await state.get_data()
    style = await get_style_by_id(data["style_id"], message.from_user.id)
    if not style:
        await message.answer("Style not found.", reply_markup=main_keyboard())
        await state.clear()
        return

    cost = num * STARS_PER_IMAGE
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        await message.answer("👑 Admin — Free generation")
        await do_generate(message, data["character"], style, num)
        await state.clear()
        return

    balance = await get_balance(user_id)
    if balance < cost:
        await message.answer(
            f"❌ Not enough Stars!\n"
            f"Need: {cost} ⭐\n"
            f"Your balance: {balance} ⭐\n\n"
            f"Use Deposit to top up.",
            reply_markup=main_keyboard()
        )
        await state.clear()
        return

    success = await deduct_balance(user_id, cost)
    if not success:
        await message.answer("Error deducting balance.", reply_markup=main_keyboard())
        await state.clear()
        return

    new_balance = await get_balance(user_id)
    await message.answer(f"✅ {cost} ⭐ deducted. Remaining: {new_balance} ⭐")
    await do_generate(message, data["character"], style, num)
    await state.clear()

async def do_generate(message: Message, character: str, style, num: int):
    await message.answer("Generating images... Please wait.")
    results = await generate_images(
        character_name=character,
        style_description=style[4],
        reference_image_path=style[3],
        num_images=num
    )
    for res in results:
        if res.startswith("http"):
            await message.answer_photo(res)
        else:
            await message.answer(res)
    await message.answer("✅ Generation completed!", reply_markup=main_keyboard())

async def main():
    await init_db()
    print("Bot starting with Wallet + Deposit History...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
