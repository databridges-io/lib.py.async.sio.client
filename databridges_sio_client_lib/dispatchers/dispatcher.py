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

from ..exceptions import dBError


class dispatcher:
    def __init__(self):
        self.__local_register = {}
        self.__global_register = []

    def isExists(self, eventName):
        if eventName  in self.__local_register:
            return True
        else:
            return False

    def bind(self, eventName, callback):
        if not (eventName and not eventName.isspace()):
            raise dBError.dBError("E012")
        if not callback and not callable(callback):
            raise dBError.dBError("E013")

        if eventName not in self.__local_register:
            self.__local_register[eventName] = [callback]
        else:
            self.__local_register[eventName].append(callback)

    def bind_all(self, callback):
        if not callback and not callable(callback):
            raise dBError.dBError("E013")

        self.__global_register.append(callback)



    def unbind(self, eventName, callback):
        if not eventName and not callback:
            self.__local_register.clear()

        if eventName and not callback:
            del self.__local_register[eventName]

        if eventName and callback:
            for ca in self.__local_register[eventName]:
                if ca == callback:
                    self.__local_register[eventName].remove(ca)

    def unbind_all(self, callback):
        if not callback:
            self.__global_register.clear()
        else:
            if callback in self.__global_register:
                self.__global_register.remove(callback)

    def start_background_task(self, target, *args):
        asyncio.ensure_future(target(*args))

    async def emit2(self, eventName, channelName, sessionId, action, response):
        if eventName in self.__local_register:
            callbacks = self.__local_register[eventName]
            if len(callbacks) > 0:
                for callback in callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(channelName, sessionId, action, response)
                        self.start_background_task(callback ,  channelName, sessionId, action, response)
                        #await t
                    else:
                        callback(channelName, sessionId, action, response)



    async def emit_cf(self, functionName, inparameter, response):
        try:

            if functionName in self.__local_register:
                callbacks = self.__local_register[functionName]
                if len(callbacks) > 0:
                    for callback in callbacks:
                        if asyncio.iscoroutinefunction(callback):
                            self.start_background_task(callback ,  inparameter, response)
                            #await callback(inparameter, response)
                            #await t
                        else:
                            callback(inparameter, response)
        except Exception as e:
            pass



    async def emit_connectionState(self, eventName ,  payload=None ,  metadata=None):
        if isinstance(eventName, str):
            eventName = eventName
        else:
            eventName = eventName.value

        for callback in self.__global_register:
            if not payload and not metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback()
                    self.start_background_task(callback)
                    #await t
                else:
                    callback()

            if not payload and  metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(None , metadata)
                    self.start_background_task(callback ,  None, metadata)
                    #await t
                else:
                    callback(None , metadata)


            if  payload and  metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(payload, metadata)
                    self.start_background_task(callback ,  payload, metadata)
                    #await t
                else:
                    callback(payload, metadata)

            if  payload and not metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(payload)
                    self.start_background_task(callback,  payload)
                    #await t
                else:
                    callback(payload)

        if eventName in self.__local_register:
            callbacks = self.__local_register[eventName]
            for callback in callbacks:
                if not payload and not metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback()
                        self.start_background_task(callback)
                        #await t
                    else:
                        callback()

                if not payload and metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(None, metadata)
                        self.start_background_task(callback , None,  metadata)
                        #await t
                    else:
                        callback(None, metadata)

                if payload and metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(payload, metadata)
                        self.start_background_task(callback , payload, metadata)
                        #await t
                    else:
                        callback(payload, metadata)

                if payload and not metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(payload)
                        self.start_background_task(callback ,  payload)
                        #await t
                    else:
                        callback(payload)

    async def emit_channel(self, eventName, payload=None, metadata=None):
        if isinstance(eventName, str):
            eventName = eventName
        else:
            eventName = eventName.value

        await self.emit_connectionState(eventName, payload, metadata)



    async def emit_clientfunction(self, functionName, inparameter, response=None, rsub=None):

        if isinstance(functionName, str):
            functionName = functionName
        else:
            functionName = functionName.value

        if functionName in self.__local_register:
            callbacks = self.__local_register[functionName]
            for callback in callbacks:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(inparameter , response)
                    self.start_background_task(callback , inparameter , response )
                else:
                    callback(inparameter , response)


    async def emit_clientfunction2(self, functionName, inparameter, response=None, rsub=None):

        if isinstance(functionName, str):
            functionName = functionName
        else:
            functionName = functionName.value

        if functionName in self.__local_register:
            callbacks = self.__local_register[functionName]
            for callback in callbacks:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(inparameter , response, rsub)
                    self.start_background_task(callback, inparameter , response, rsub)
                else:
                    callback(inparameter , response, rsub)


    async def emit(self, eventNameT, EventInfo=None, channelName=None, metadata=None):
        if isinstance(eventNameT, str):
            eventName = eventNameT
        else:
            eventName = eventNameT.value

        for callback in self.__global_register:
            if EventInfo and channelName and metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(eventName, channelName, EventInfo, metadata)
                    self.start_background_task(callback ,eventName, channelName, EventInfo, metadata)
                else:
                    callback(eventName, channelName, EventInfo, metadata)


            if EventInfo and channelName and not metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(eventName, channelName, EventInfo)
                    self.start_background_task(callback, eventName, channelName, EventInfo)
                else:
                    callback(eventName, channelName, EventInfo)


            if EventInfo and not channelName and metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(eventName, EventInfo, metadata)
                    self.start_background_task(callback, eventName, EventInfo, metadata)
                else:
                    callback(eventName, EventInfo, metadata)


            if EventInfo and not channelName and not metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(eventName, EventInfo)
                    self.start_background_task(callback, eventName, EventInfo)
                else:
                    callback(eventName, EventInfo)


            if not EventInfo and not channelName and not metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(eventName)
                    self.start_background_task(callback, eventName)
                else:
                    callback(eventName)



            if not EventInfo and channelName and not metadata:
                if asyncio.iscoroutinefunction(callback):
                    #await callback(eventName, channelName)
                    self.start_background_task(callback, eventName, channelName)
                else:
                    callback(eventName, channelName)

        if eventName in self.__local_register:
            callbacks = self.__local_register[eventName]
            for callback in callbacks:
                if EventInfo and channelName and metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(eventName, channelName, EventInfo, metadata)
                        self.start_background_task(callback, eventName, channelName , EventInfo, metadata)
                    else:
                        callback(eventName, channelName, EventInfo, metadata)

                if EventInfo and channelName and not metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(eventName, channelName, EventInfo)
                        self.start_background_task(callback, eventName, channelName,  EventInfo)
                    else:
                        callback(eventName, channelName, EventInfo)
                        

                if EventInfo and not channelName and metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(eventName, EventInfo, metadata)
                        self.start_background_task(callback, eventName, EventInfo, metadata)
                        
                    else:
                        callback(eventName, EventInfo, metadata)

                if EventInfo and not channelName and not metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(eventName, EventInfo)
                        self.start_background_task(callback, eventName, EventInfo)
                        
                    else:
                        callback(eventName, EventInfo)

                if not EventInfo and not channelName and not metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(eventName)
                        self.start_background_task(callback, eventName,)
                    else:
                        callback(eventName)

                if not EventInfo and channelName and not metadata:
                    if asyncio.iscoroutinefunction(callback):
                        #await callback(eventName, channelName)
                        self.start_background_task(callback, eventName, channelName)
                    else:
                        callback(eventName, channelName)
