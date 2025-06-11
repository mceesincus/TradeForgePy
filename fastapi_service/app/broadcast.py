# fastapi_service/app/broadcast.py
import asyncio
import logging
from typing import Set

from tradeforgepy.core.models_generic import GenericStreamEvent

logger = logging.getLogger(__name__)

class Broadcast:
    """
    A simple broadcast utility that distributes events to multiple asyncio Queues.
    It also manages which provider contracts are currently being subscribed to.
    """
    def __init__(self):
        self._client_queues: Set[asyncio.Queue] = set()
        self.subscribed_contracts: Set[str] = set()
        logger.info("Broadcast instance created.")

    async def _cleanup_queue(self, queue: asyncio.Queue):
        """Removes a queue from the set of active clients."""
        if queue in self._client_queues:
            self._client_queues.remove(queue)

    async def subscribe(self, queue: asyncio.Queue):
        """A new client subscribes to receive events."""
        self._client_queues.add(queue)
        logger.info(f"New client subscribed. Total clients: {len(self._client_queues)}")

    async def unsubscribe(self, queue: asyncio.Queue):
        """A client unsubscribes from events."""
        await self._cleanup_queue(queue)
        logger.info(f"Client unsubscribed. Total clients: {len(self._client_queues)}")

    async def publish(self, event: GenericStreamEvent):
        """
        Receives an event from the provider and puts it into each client's queue.
        This method will be the main callback for the provider's `on_event`.
        """
        # We iterate over a copy of the set in case the set is modified
        # during iteration (e.g., a client disconnects).
        for queue in list(self._client_queues):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("A client's queue was full. Event dropped for that client.")
            except Exception as e:
                logger.error(f"Error putting event into a client's queue: {e}")