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

class Promise:
    def __init__(self):
        self.resolved = ''
        self.rejected = ''


    async def Execute(self, callback):
        self.resolved = ''
        self.rejected = ''
        if asyncio.iscoroutinefunction(callback):
            await callback(self.resolve, self.reject)
        else:
            await callback(self.resolve, self.reject)

    def resolve(self, value):
        self.resolved = value

    def reject(self, value):
        self.rejected = value

    def then(self, callback):
        if not self.rejected:
            self.resolved = callback(self.resolved)
        return self

    def catch(self, callback):
        if self.rejected:
            self.rejected = callback(self.rejected)
        return self
