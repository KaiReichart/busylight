"""BusyLight MQTT
"""
import asyncio

from loguru import logger
from os import environ

from ..color import parse_color_string
from ..manager import LightManager
from ..lights import NoLightsFound
from ..effects import Effects

import typer
from paho.mqtt import client as mqtt

__description__ = """
<!-- markdown formatted for HTML rendering -->
An MQTT client for USB connected presence lights.

[Source](https://github.com/JnyJny/busylight.git)
"""

class BusylightMQTT():

    def __init__(self, manager: LightManager, ctx: typer.Context, host: str, port: int, topic: str):
        self.loop = asyncio.get_event_loop()
        logger.info("Initialize the server.")
        self.topic = topic
        self.manager = manager
        self.ctx = ctx

        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect(host, port, 60)


# The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        try:
            print(msg.topic+" "+str(msg.payload))
            color_string = msg.payload.decode("utf-8")
            color = parse_color_string(color_string)
            steady = Effects.for_name("steady")(color)
            print (f"Applying effect {steady}")
            asyncio.run_coroutine_threadsafe(
                self.apply_effect_async(steady, self.ctx.obj.lights, timeout=self.ctx.obj.timeout),
                self.loop
            )

        except Exception as e:
            print(f"Failed to process message: {e}")

    async def apply_effect_async(self, effect, light_ids, timeout):
        print ("applying effect")
        await self.manager.effect_supervisor(effect, self.manager.selected_lights(light_ids), timeout)


    def run(self):
        logger.info("Run the server.")
        self.mqttc.loop_start()

        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            self.manager.off(self.ctx.obj.lights)
            self.mqttc.loop_stop()
            pass
