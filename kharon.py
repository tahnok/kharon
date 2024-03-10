"""
Kharon: ferry data from MQTT to postgres

Currently only supports loading simple floating point numbers from MQTT into postgres
"""
from datetime import datetime, timezone
import json
from typing import cast

import asyncio
from aiomqtt import Client, Message
import psycopg
from pydantic import BaseModel

messages = asyncio.Queue()

class MqttConfig(BaseModel):
    hostname: str
    username: str
    password: str | None


class Config(BaseModel):
    mqtt: MqttConfig
    postgres_url: str
    topics_to_tables: dict[str,str]


class Reading(BaseModel):
    kind: str
    value: float
    observed_at: datetime

    @classmethod
    def from_mqtt(cls, config: Config, message: Message, observed_at: datetime) -> 'Reading':
        kind = config.topics_to_tables[message.topic.value]
        value = float(message.payload.decode("utf-8"))
        return cls(kind=kind, value=value, observed_at=observed_at)

async def db_task(postgres_url: str):
    async with await psycopg.AsyncConnection.connect(postgres_url) as aconn:
        while True:
            reading = cast(Reading, await messages.get())
            async with aconn.cursor() as acur:
                await acur.execute(
                    f"INSERT INTO {reading.kind} (value, observed_at) VALUES (%s, %s)",
                    (reading.value, reading.observed_at))
                await aconn.commit()


async def mqtt_task(config: Config):
    # problem: this doesn't handle dropping internet / restarting
    async with Client(hostname=config.mqtt.hostname, username=config.mqtt.username, password=config.mqtt.password) as client:
        for topic in config.topics_to_tables:
            await client.subscribe(topic)
        async for message in client.messages:
            now = datetime.now(timezone.utc)
            reading = Reading.from_mqtt(config, message, now)
            print(reading)

            # ignore retained messages to avoid double inserting values
            # this means we may drop / loose some messages while disconnected but oh well
            if message.retain == 0:
                messages.put_nowait(reading)

async def main(config: Config):
    async with asyncio.TaskGroup() as tg:
        tg.create_task(mqtt_task(config))
        tg.create_task(db_task(config.postgres_url))

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = Config(**json.load(f))
    asyncio.run(main(config))
