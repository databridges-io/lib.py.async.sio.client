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
from ..dispatchers import dispatcher
from ..events import dBConnectionEvents
from ..commonUtils import util

from ..messageTypes import dBTypes
import time

from ..exceptions import dBError


class connectStates:
    def __init__(self, dBCoreObject):
        self.state = ""
        self.isconnected = False
        self.__registry = dispatcher.dispatcher()
        self.__newLifeCycle = True
        self.reconnect_attempt = 0
        self.__dbcore = dBCoreObject
        self.rttms = None
        self.__inner_connectList = [dBConnectionEvents.states.CONNECTED, dBConnectionEvents.states.RECONNECTED,
                                    dBConnectionEvents.states.RTTPONG, dBConnectionEvents.states.RTTPING]

    async def rttping(self, payload=None):
        t1 = round(time.time() )
        m_status = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.SYSTEM_MSG, None, None, payload,
                                           "rttping",
                                           None,
                                            t1,
                                           None)
        if not m_status:
            raise dBError.dBError("E011")

    def set_newLifeCycle(self, value):
        self.__newLifeCycle = value

    def get_newLifeCycle(self):
        return self.__newLifeCycle;

    def bind(self, eventName, callback):
        if not (eventName and not eventName.isspace()):
            raise dBError.dBError("E012")

        if not callback and not callable(callback):
            raise dBError.dBError("E013")

        if eventName not in dBConnectionEvents.connectionEvent:
            raise dBError.dBError("E012")
        self.__registry.bind(eventName, callback);

    def unbind(self, eventName, callback=None):
        try:
            self.__registry.unbind(eventName, callback)
        except Exception as e:
            pass


    def updatestates(self, eventName):
        if eventName in self.__inner_connectList:
            self.isconnected = True
        else:
            self.isconnected = False

    async def handledispatcher(self, eventName, eventInfo=None):
        try:
            previous = self.state
            if eventName.value not in ["reconnect_attempt", 'rttpong']:
                self.state = eventName.value;
            self.updatestates(eventName)

            if eventName != previous:
                if eventName.value != "reconnect_attempt":
                    if eventName.value not in ["reconnect_attempt", "rttpong"]:
                        if previous not in ["reconnect_attempt", "rttpong"]:
                            leventInfo = {"previous": previous, "current": eventName.value}
                            self.state = eventName.value
                            
                            if eventName.value == "disconnected":
                                self.state = ""

                            await self.__registry.emit_connectionState(dBConnectionEvents.states.STATE_CHANGE, leventInfo)

            if eventInfo:
                await self.__registry.emit_connectionState(eventName, eventInfo)
            else:
                await self.__registry.emit_connectionState(eventName, None)

            if eventName == "reconnected":
                self.state = "connected"
        except Exception as e:
            pass