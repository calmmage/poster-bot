from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from botspot import commands_menu
from botspot.utils import send_safe

from src.app import App, Readiness

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
    from botspot.user_interactions import ask_user_choice

    assert message.from_user is not None
    user_id = message.from_user.id

    # save user message to queue
    # todo: handle captions, media etc. 
    # todo: for now, add 'forwarding' mode for media-based posts
    post_content = await app.prepare_post_content(message)

    # todo: move to prepare_post_content?
    # title = app._get_post_title(post_content)

    preview = f"Adding new post to queue. Preview:\n'''\n{post_content}\n'''\nHow ready is this post?"
    choices = {
        "finished": "Finished",
        "unpolished": "Unpolished",
        "draft": "Draft",
        "cancel": "Cancel"
    }
    choice = await ask_user_choice(
        message.chat.id,
        preview,
        choices=choices,
        default_choice="draft",
        state=state,
        parse_mode="HTML", 
        cleanup=True,
    )
    if choice == "cancel" or choice is None:
        await send_safe(message.chat.id, "Cancelled.")
        return
    readiness_map = {
        "finished": Readiness.FINISHED,
        "unpolished": Readiness.UNPOLISHED,
        "draft": Readiness.DRAFT
    }
    readiness = readiness_map[choice]
    await app.add_to_queue(post_content, user_id, readiness=readiness)

    # todo: add alternative mode of saving: forwarding
    queue_items = await app.queue.get_items(user_id=user_id)
    # todo: add better stats
    # counts per readiness state
    unposted_items = [item for item in queue_items if not item.posted]

    # todo: Format this message better, add utils
    # - util to get queue stats - here and in app.py send_to_channel
    # - util to format post preview - here and above
    await send_safe(
        message.chat.id,
        f"Saved to queue as {choice}. Currently in queue: {len(unposted_items)}. Preview:</b>\n{post_content}\n\nReadiness: {readiness.value}",
        parse_mode="HTML"
    )