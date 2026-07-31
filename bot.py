import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, STYLES_DIR
from database import init_db, add_style, get_user_styles, get_style_by_id
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

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to **StyleForge Bot** 🎨\n\n"
        "I can generate high-quality images of any character using your custom art styles.\n\n"
        "Available commands:\n"
        "• /add_style – Upload a new style reference image\n"
        "• /list_styles – View all your saved styles\n"
        "• /generate – Generate images using a saved style\n"
        "• /help – Show help message"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "**How to use the bot:**\n\n"
        "1. Use /add_style and send a reference image\n"
        "2. Give your style a name\n"
        "3. Use /generate → choose a style → enter character name → enter number of images (1-10)\n\n"
        "The bot will generate images matching the style and quality of your reference."
    )

@dp.message(Command("add_style"))
async def add_style_cmd(message: Message, state: FSMContext):
    await message.answer("Please send me the style reference image now:")
    await state.set_state(Form.waiting_style_name)

@dp.message(Form.waiting_style_name, F.photo)
async def process_style_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    file_path = os.path.join(STYLES_DIR, f"{message.from_user.id}_{photo.file_id}.jpg")
    await bot.download_file(file.file_path, file_path)
    
    await state.update_data(image_path=file_path)
    await message.answer("Image received. Now please send a name for this style (example: soft_anime):")

@dp.message(Form.waiting_style_name, F.text)
async def process_style_name(message: Message, state: FSMContext):
    data = await state.get_data()
    image_path = data.get("image_path")
    
    if not image_path:
        await message.answer("Something went wrong. Please try again with /add_style")
        await state.clear()
        return
    
    name = message.text.strip()
    description = await analyze_style(image_path)
    
    await add_style(message.from_user.id, name, image_path, description)
    await message.answer(f"✅ Style saved successfully as: **{name}**")
    await state.clear()

@dp.message(Command("list_styles"))
async def list_styles(message: Message):
    styles = await get_user_styles(message.from_user.id)
    if not styles:
        await message.answer("You don't have any saved styles yet.\nUse /add_style to add one.")
        return
    
    text = "Your saved styles:\n\n"
    for s in styles:
        text += f"ID: {s[0]} | Name: {s[1]}\n"
    
    await message.answer(text)

@dp.message(Command("generate"))
async def generate_cmd(message: Message, state: FSMContext):
    styles = await get_user_styles(message.from_user.id)
    if not styles:
        await message.answer("No styles found. Please add a style first using /add_style")
        return
    
    builder = InlineKeyboardBuilder()
    for s in styles:
        builder.button(text=f"{s[1]} (ID: {s[0]})", callback_data=f"style_{s[0]}")
    builder.adjust(1)
    
    await message.answer("Select a style to use:", reply_markup=builder.as_markup())
    await state.set_state(Form.waiting_style_choice)

@dp.callback_query(F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext):
    style_id = int(callback.data.split("_")[1])
    await state.update_data(style_id=style_id)
    await callback.message.answer("Enter the character name (example: zero two, rem, asuna):")
    await state.set_state(Form.waiting_character)
    await callback.answer()

@dp.message(Form.waiting_character)
async def process_character(message: Message, state: FSMContext):
    await state.update_data(character=message.text.strip())
    await message.answer("How many images do you want? (Enter a number from 1 to 10):")
    await state.set_state(Form.waiting_num_images)

@dp.message(Form.waiting_num_images)
async def process_num_images(message: Message, state: FSMContext):
    try:
        num = int(message.text.strip())
        if num < 1 or num > 10:
            await message.answer("Please enter a number between 1 and 10")
            return
    except:
        await message.answer("Please enter a valid number")
        return
    
    data = await state.get_data()
    style = await get_style_by_id(data["style_id"], message.from_user.id)
    
    if not style:
        await message.answer("Style not found.")
        await state.clear()
        return
    
    await message.answer("Generating images... Please wait a moment.")
    
    results = await generate_images(
        character_name=data["character"],
        style_description=style[4],
        reference_image_path=style[3],
        num_images=num
    )
    
    for res in results:
        await message.answer(res)
    
    await message.answer("✅ Generation completed!\n(Currently in test mode – real image generation will be connected soon)")
    await state.clear()

async def main():
    await init_db()
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())