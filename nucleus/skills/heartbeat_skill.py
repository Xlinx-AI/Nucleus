from nucleus.skill_manager import Skill
import asyncio

class HeartbeatSkill(Skill):
    """
    This skill sends heartbeat signals at a given interval.
    Use it to monitor agents, services, or just to feel alive during long runs.
    """
    def __init__(self, event_bus=None):
        super().__init__(
            name="heartbeat",
            description="Sends heartbeat signals at a set interval.",
            capability=None
        )
        self.event_bus = event_bus
        self._task = None
        self._running = False

    def set_event_bus(self, bus):
        self.event_bus = bus

    def get_capabilities(self):
        return [
            {
                "intent": "Start heartbeat",
                "desc": "Starts sending heartbeat signals.",
                "input_type": "interval",
                "output_type": "none",
                "tags": ["heartbeat", "monitor", "async"]
            },
            {
                "intent": "Stop heartbeat",
                "desc": "Stops sending heartbeat signals.",
                "input_type": "none",
                "output_type": "none",
                "tags": ["heartbeat", "monitor", "async"]
            }
        ]

    async def execute_async(self, step: dict, context: dict = None):
        """
        Give me an intent ("Start heartbeat" or "Stop heartbeat") and I'll do my thing.
        """
        intent = step.get("intent", "").lower()
        if "start" in intent:
            interval = step.get("interval", 5)
            self.start(interval)
            return {"status": "started", "interval": interval}
        elif "stop" in intent:
            self.stop()
            return {"status": "stopped"}
        else:
            return {"error": "Unknown heartbeat intent."}

    def start(self, interval):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_heartbeat(interval))

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_heartbeat(self, interval):
        while self._running:
            print("💓 Heartbeat signal sent")
            await asyncio.sleep(interval)