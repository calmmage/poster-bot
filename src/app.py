from enum import Enum
from typing import Any
from pydantic_settings import BaseSettings
from botspot.components.new.queue_manager import create_queue, QueueItem
from botspot.components.main.event_scheduler import get_scheduler
from typing import Optional
from datetime import datetime
from pydantic import model_validator, SecretStr
from croniter import croniter
from botspot.utils import send_safe
from loguru import logger
from botspot.components.data.user_data import User
import random
from src.utils import validate_cron_expr


class SchedulingMode(Enum):
    PERIOD = "period"
    CRON = "cron"

class AppConfig(BaseSettings):
    """Basic app configuration"""

    telegram_bot_token: SecretStr
    target_channel_id: int
    scheduling_mode: SchedulingMode = SchedulingMode.PERIOD
    scheduling_period_seconds: int = 60
    scheduling_cron_expr: Optional[str] = None
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


    @model_validator(mode="after")
    def check_cron_expr_if_cron(self):
        if self.scheduling_mode == SchedulingMode.CRON:
            if not self.scheduling_cron_expr:
                raise ValueError(
                    "scheduling_cron_expr must be set when scheduling_mode is CRON"
                )
            if isinstance(self.scheduling_cron_expr, list):
                logger.warning(
                    f"'{self.scheduling_cron_expr=}' is a list, converting to string."
                )
                self.scheduling_cron_expr = " ".join(self.scheduling_cron_expr)
            # Validate cron expression
            validate_cron_expr(self.scheduling_cron_expr)
        return self


class SaveMode(Enum):
    DATA = "data"  # save data to db and then post manually
    FORWARD = (
        "forward"  # save message id to db and then forward original message to channel
    )


class Readiness(Enum):
    DRAFT = "draft"
    UNPOLISHED = "unpolished"
    FINISHED = "finished"


class PosterBotQueueItem(QueueItem):
    posted: bool = False
    posted_channel_id: Optional[int] = None
    posted_at: Optional[datetime] = None
    # todo: readiness - enum
    # todo: topic(s) - set of enums


class PosterBotUser(User):
    target_channel_id: int | None = None
    scheduling_mode: SchedulingMode | None = None
    scheduling_period_seconds: int | None = None
    scheduling_cron_expr: str | None = None
    auto_posting_enabled: bool = False


class App:
    name = "Poster Prototype Bot"

    def __init__(self, **kwargs):
        self.config = AppConfig(**kwargs)

        self._queue = None
        self._scheduler = None

    @property
    def queue(self):
        if self._queue is None:
            self._queue = create_queue(key="content", item_model=PosterBotQueueItem)
        return self._queue

    @property
    def scheduler(self):
        if self._scheduler is None:
            self._scheduler = get_scheduler()
        return self._scheduler

    async def add_to_queue(self, text: str, user_id: int):
        item = PosterBotQueueItem(data=text)
        await self.queue.add_item(item, user_id=user_id)

    async def get_users(self) -> list[PosterBotUser]:
        from botspot.utils import get_user_manager

        user_manager = get_user_manager()
        return await user_manager.get_users()

    async def schedule_posts_on_startup(self):
        """Schedule posting from queue at regular intervals or cron."""

        # go over all existing users and schedule posting job if they have auto-posting enabled
        users = await self.get_users()

        for user in users:
            if user.auto_posting_enabled:
                logger.info(
                    f"Scheduling posts for user {user.user_id} to channel {user.target_channel_id}"
                )
                self._schedule_user_posting_job(user)
            else:
                logger.info(
                    f"Auto-posting is disabled for user {user.user_id}, skipping scheduling."
                )

    def _schedule_user_posting_job(self, user: PosterBotUser):
        """
        Schedule a posting job for a user based on their settings.
        """
        logger.debug(f"_schedule_user_posting_job called with user_id={user.user_id}")
        assert user.scheduling_mode is not None, "Scheduling mode is not set for user"

        if user.scheduling_mode == SchedulingMode.PERIOD:
            assert (
                user.scheduling_period_seconds is not None
            ), "Scheduling period is not set for user"

            logger.debug(
                f"Scheduling user {user.user_id} to post every {user.scheduling_period_seconds} seconds"
            )
            self.scheduler.add_job(
                func=self.post_content_job,
                trigger="interval",
                seconds=user.scheduling_period_seconds,
                args=[user.user_id],
                id=f"post_content_job_{user.user_id}",
            )
        elif user.scheduling_mode == SchedulingMode.CRON:
            assert (
                user.scheduling_cron_expr is not None
            ), "Scheduling cron expression is not set for user"

            logger.debug(
                f"Scheduling user {user.user_id} to post with cron {user.scheduling_cron_expr}"
            )
            self.scheduler.add_job(
                func=self.post_content_job,
                trigger="cron",
                args=[user.user_id],
                id=f"post_content_job_{user.user_id}",
                cron=user.scheduling_cron_expr,
            )
        else:
            raise ValueError(f"Invalid scheduling mode: {user.scheduling_mode}")

    async def post_content_job(self, user_id: int):
        """
        A job that runs on a schedule for a particular user.
        """

        user = await self.get_user(user_id)

        post = await self._pick_post_from_queue(user_id)
        channel_id = user.target_channel_id
        assert channel_id is not None, "Target channel ID is not set for user"

        if not post:
            logger.info(f"No posts in queue for user {user_id}")
            # notify the user.
            await send_safe(
                user_id,
                "Scheduled posting time is due, but there are no posts in queue to post.",
            )
            return

        await send_safe(channel_id, post.data)
        logger.info(f"Posted content to channel {channel_id}: {post.data}")

        # Notify the user that the post was sent, and the amount of remaining posts in queue
        all_posts = await self.queue.get_items(user_id=user_id)
        remaining_posts = [item for item in all_posts if not item.posted]
        await send_safe(
            user_id,
            f"Your post was sent to the channel. Remaining posts in queue: {len(remaining_posts) - 1}",
        )

        # Mark the post as posted
        post.posted = True
        post.posted_channel_id = channel_id
        post.posted_at = datetime.now()
        await self.queue.update_item(post)

    async def _pick_post_from_queue(self, user_id: int) -> PosterBotQueueItem | None:
        """
        Pick a post from the queue for a user.
        """
        logger.debug(f"_pick_post_from_queue called with user_id={user_id}")
        all_posts = await self.queue.get_items(user_id=user_id)
        if not all_posts:
            logger.info(f"No posts in queue for user {user_id}")
            return None

        # todo: implement a special method that picks the item to be posted
        #  make sure post is ready - not an unfinished draft (for this channel - for when we add multiple channels)
        non_posted = [item for item in all_posts if not item.posted]
        if not non_posted:
            logger.info(f"No non-posted items in queue for user {user_id}")
            return None

        return random.choice(non_posted)

    async def activate_user(self, user_id: int):
        """
        Activate a user.
        """
        logger.info(f"Activating user {user_id}")
        # check if user has all the settings specified. if not - launch the setup flow
        user = await self.get_user(user_id)
        # if user.scheduling_mode is None:
        await self._initialize_user(user_id)

        await self.update_user_field(user_id, "auto_posting_enabled", True)
        # re-load the user object to get the updated values
        user = await self.get_user(user_id)

        self._schedule_user_posting_job(user)

    async def deactivate_user(self, user_id: int):
        """
        Deactivate a user.
        """
        logger.info(f"Deactivating user {user_id}")
        await self.update_user_field(user_id, "auto_posting_enabled", False)
        # todo: check if user has a job scheduled. if so - cancel it.
        self._cancel_user_posting_job(user_id)

    def _cancel_user_posting_job(self, user_id: int):
        """
        Cancel the posting job for a user.
        """
        logger.debug(f"_cancel_user_posting_job called with user_id={user_id}")
        self.scheduler.remove_job(f"post_content_job_{user_id}")

    async def get_user(self, user_id: int) -> PosterBotUser:
        from botspot.utils import get_user_manager

        user_manager = get_user_manager()
        user = await user_manager.get_user(user_id)
        assert isinstance(user, PosterBotUser), f"User {user_id} is not a PosterBotUser"
        return user

    async def update_user_field(self, user_id: int, field: str, value: Any):
        from botspot.utils import get_user_manager

        user_manager = get_user_manager()
        await user_manager.update_user(user_id, field, value)

    async def _initialize_user(self, user_id: int):
        logger.debug(f"_initialize_user called with user_id={user_id}")
        data = self.config.model_dump(mode="json")
        for key in [
            "target_channel_id",
            "scheduling_mode",
            "scheduling_period_seconds",
            "scheduling_cron_expr",
        ]:
            await self.update_user_field(user_id, key, data[key])
        # todo: replace with a proper interactive flow
