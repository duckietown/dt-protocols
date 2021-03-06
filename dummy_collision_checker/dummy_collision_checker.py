from aido_schemas import Context
from dt_protocols import CollisionCheckQuery, CollisionCheckResult, MapDefinition

__all__ = ["DummyCollisionChecker"]


class DummyCollisionChecker:
    def init(self, context: Context):
        context.info("init()")

    def on_received_set_params(self, context: Context, data: MapDefinition):
        pass

    def on_received_query(self, context: Context, data: CollisionCheckQuery):
        result = CollisionCheckResult(True)
        context.write("response", result)

    def finish(self, context: Context):
        context.info("finish()")
