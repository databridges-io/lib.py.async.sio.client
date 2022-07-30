"""
	Databridges Python client Library
	https://www.databridges.io/



	Copyright 2022 Optomate Technologies Private Limited.

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

	    http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.
"""

import asyncio
class Timer:
    def __init__(self, delay, callback):
        self._future = asyncio.ensure_future(
            self._schedule_delayed_task(
                delay,
                callback,
            ))

    @classmethod
    async def _schedule_delayed_task(cls, delay,
                                     callback):
        await asyncio.sleep(delay)
        if asyncio.iscoroutinefunction(callback):
            await callback()
        else:
            callback()

    async def wait(self):
        await self._future

    def cancel(self):
        self._future.cancel()
