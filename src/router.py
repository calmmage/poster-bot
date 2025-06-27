from src.app import App
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from botspot import commands_menu
from botspot.utils import send_safe

router = Router()


@commands_menu.botspot_command("start", "Start the bot")
@router.message(CommandStart())
async def start_handler(message: Message, app: App):
    await send_safe(message.chat.id, f"Hello! Welcome to {app.name}!")


@commands_menu.botspot_command("help", "Show this help message")
@router.message(Command("help"))
async def help_handler(message: Message, app: App):
    """Basic help command handler"""
    # todo: write a proper help message
    await send_safe(message.chat.id, f"This is {app.name}. Use /start to begin.")



@commands_menu.botspot_command("start_autopost", "Enable auto-posting")
@router.message(Command("start_autopost"))
async def start_autopost_handler(message: Message, app: App):
    """Enable auto-posting for the user"""
    assert message.from_user is not None
    # todo: check if active - if so - notify the user that was already active
    await app.activate_user(message.from_user.id)
    await message.answer("Auto-posting enabled!")


@commands_menu.botspot_command("stop_autopost", "Disable auto-posting")
@router.message(Command("stop_autopost"))
async def stop_autopost_handler(message: Message, app: App):
    """Disable auto-posting for the user"""
    assert message.from_user is not None
    # todo: check if active - if not - notify the user that was already inactive
    await app.deactivate_user(message.from_user.id)
    await message.answer("Auto-posting disabled!")



@router.message(F.text | F.caption)
async def message_handler(message: Message, app: App, state: FSMContext):
    """Basic help command handler"""
    assert message.from_user is not None
    user_id = message.from_user.id

    # save user message to queue
    # todo: handle captions, media etc.
    await app.add_to_queue(message.html_text, user_id)
    # todo: add confirmation before adding to queue
    from botspot.user_interactions import ask_user_confirmation
    confirmed = await ask_user_confirmation(message.chat.id, "Are you sure you want to add this to queue?", state=state)
    if not confirmed:
        await send_safe(message.chat.id, "Cancelled.")
        return

    # todo: add alternative mode of saving: forwarding
    total_queue_items = await app.queue.get_items(user_id=user_id)

    # todo: add better stats
    # 1) ...
    # 2) counts per readiness state
    await send_safe(
        message.chat.id, f"Saved to queue. Currenlty in queue: {len(total_queue_items)}"
    )