from kinto.core import logger
from kinto.core.listeners import ListenerBase
from kinto.core.utils import json

from kinto_redis.storage import create_from_config


class Listener(ListenerBase):
    """
    A Redis-based event listener that simply pushes the events payloads into
    the specified Redis list as they happen.

    This listener allows actions to be performed asynchronously, using Redis
    Pub/Sub notifications, or scheduled inspections of the queue.
    """

    def __init__(self, client, listname, *args, **kwargs):
        super(Listener, self).__init__(*args, **kwargs)
        self._client = client
        self.listname = listname

    def __call__(self, event):
        try:
            payload = json.dumps({"payload":event.payload,"impacted_objects":event.impacted_objects})
        except TypeError:
            logger.error("Unable to dump the payload", exc_info=True)
            return
        try:
            self._client.lpush(self.listname, payload)
        except Exception:
            logger.error("Unable to send the payload to Redis", exc_info=True)


def load_from_config(config, prefix):
    settings = config.get_settings()
    settings.setdefault(prefix + "url", "")
    settings.setdefault(prefix + "pool_size", 25)
    listname = settings.get(prefix + "listname", "kinto.core.events")
    client = create_from_config(config, prefix)
    return Listener(client, listname=listname)
