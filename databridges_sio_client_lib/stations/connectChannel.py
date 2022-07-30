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

from ..messageTypes import dBTypes

from ..commonUtils import util, aioPromise
from ..dispatchers import dispatcher
from ..exceptions import dBError
from ..events import dBEvents

connectSupportedEvents = [dBEvents.systemEvents.CONNECT_SUCCESS.value,
                          dBEvents.systemEvents.CONNECT_FAIL.value,
                          dBEvents.systemEvents.RECONNECT_SUCCESS.value,
                          dBEvents.systemEvents.RECONNECT_FAIL.value,
                          dBEvents.systemEvents.DISCONNECT_SUCCESS.value,
                          dBEvents.systemEvents.DISCONNECT_FAIL.value,
                          dBEvents.systemEvents.ONLINE.value,
                          dBEvents.systemEvents.OFFLINE.value,
                          dBEvents.systemEvents.REMOVE.value,
                          dBEvents.systemEvents.PARTICIPANT_JOINED.value,
                          dBEvents.systemEvents.PARTICIPANT_LEFT.value]


class channelnbd():
    def __init__(self, channelName, sid, dBCoreObject):
        self.__channelName = channelName
        self.__sid = sid
        self.__dbcore = dBCoreObject
        self.__isOnline = False
        self.__dispatch = dispatcher.dispatcher()

    def getChannelName(self):
        return self.__channelName

    def isOnline(self):
        return self.__isOnline

    def set_isOnline(self, value):
        self.__isOnline = value

    async def publish(self, eventName, eventData, seqnum=None):
        if not self.__isOnline:
            raise dBError.dBError("E014")

        if str(self.__channelName).lower() == "sys:*":
            raise dBError.dBError("E015")

        if not eventName:
            raise dBError.dBError("E058")
        if type(eventName) is not str:
            raise dBError.dBError("E059")

        m_status = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.PUBLISH_TO_CHANNEL,
                                                 self.__channelName, None,
                                                 eventData, eventName, None, None, seqnum)

        if not m_status:
            raise dBError.dBError("E014")


    def bind(self, eventName, callback):
        if eventName in connectSupportedEvents:
            if not self.__dispatch.isExists(eventName):
                self.__dispatch.bind(eventName, callback)
        else:
            raise dBError.dBError("E103")

    def unbind(self, eventName, callback):
        if eventName in connectSupportedEvents:
            if self.__dispatch.isExists(eventName):
                self.__dispatch.unbind(eventName, callback)

    async def emit(self, eventName, EventInfo, channelName=None, metadata=None):
        self.__dispatch.emit(eventName, EventInfo, channelName, metadata)

    async def emit_channel(self, eventName, EventInfo,  metadata):
        await self.__dispatch.emit_channel(eventName, EventInfo,  metadata)


    async def call(self , functionName ,  payload ,  ttl , callback):
        async def _incall(resolve , reject):
            def successResolve(value):
                #self.__dbcore.rpc.ClearChannel(self.__channelName)
                resolve(value)

            def successReject(value):
                #self.__dbcore.rpc.ClearChannel(self.__channelName)
                reject(value)

            if functionName not in ['channelMemberList', 'channelMemberInfo', 'timeout' ,  'err']:
                reject(dBError.dBError("E038"))
            else:
                if str(self.__channelName).lower().startswith("prs:") or str(self.__channelName).lower().startswith("sys:"):
                    caller = self.__dbcore.rpc.ChannelCall(self.__channelName)
                    p =   await caller.call(functionName ,  payload ,  ttl ,  callback)
                    p.then(successResolve).catch(successReject)
                else:
                    reject(dBError.dBError("E039"))

        pr = aioPromise.Promise()
        await pr.Execute(_incall)
        return pr