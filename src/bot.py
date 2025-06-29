from pathlib import Path

from calmlib.utils import setup_logger, LogFormat #, heartbeat_for_sync
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from src.app import App, PosterBotUser
from src.router import router as main_router
from src.routers.settings import router as settings_router
from botspot.core.bot_manager import BotManager


async def on_startup(dispatcher):
    app = dispatcher["app"]
    await app.schedule_posts_on_startup()



# @heartbeat_for_sync(App.name)
def main(debug=False) -> None:
    setup_logger(logger, format=LogFormat.DEFAULT if debug else LogFormat.DETAILED, level="DEBUG" if debug else "INFO")

    # Initialize bot and dispatcher
    dp = Dispatcher()
    dp.include_router(main_router)
    dp.include_router(settings_router)

    app = App()
    dp["app"] = app

    # Initialize Bot instance with a default parse mode
    bot = Bot(
        token=app.config.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize BotManager with default components
    bm = BotManager(
        bot=bot,
        error_handler={"enabled": True},
        ask_user={"enabled": True},
        bot_commands_menu={"enabled": True},
         user_class=PosterBotUser,
    )

    # Setup dispatcher with our components
    bm.setup_dispatcher(dp)
    dp.startup.register(on_startup)

    # Start polling
    dp.run_polling(bot)


if __name__ == "__main__":
    repo_root = Path(__file__).parent
    load_dotenv(repo_root / ".env")
    main()
