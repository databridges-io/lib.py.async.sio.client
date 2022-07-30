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
import random

from ..commonUtils import aioPromise, util, aioTimer
from ..dispatchers import dispatcher
from ..exceptions import dBError
from ..messageTypes import dBTypes
from ..responseHandler import cfrpcResponse
from ..events import dBEvents
import json


class cfclient:
    def __init__(self, dBCoreObject):
        self.__dispatch = dispatcher.dispatcher()
        self.__dbcore = dBCoreObject
        self.enable = False
        self.functions = None
        self.__sid_functionname={}
        self.__callerTYPE = "cf"
        self.__functionNames = ['cf.response.tracker' , 'cf.callee.queue.exceeded']

    def verify_function(self):
        mflag = False
        if self.enable:
            if self.functions is None:
                raise dBError.dBError("E009")
            if not callable(self.functions):
                raise dBError.dBError("E010")
            mflag = True
        else:
            mflag = True
        return mflag

    def regfn(self, functionName, callback):
        if not (functionName and not functionName.isspace()):
            raise dBError.dBError("E110")
        if not callback and not callable(callback):
            raise dBError.dBError("E111")

        if functionName in  self.__functionNames:
            raise dBError.dBError("E110")

        self.__dispatch.bind(functionName, callback)


    def unregfn(self, functionName, callback):
        if functionName in self.__functionNames:
            return
        self.__dispatch.unbind(functionName, callback)




    def bind(self, eventName, callback):
        if not (eventName and not eventName.isspace()):
            raise dBError.dBError("E066")
        if not callback and not callable(callback):
            raise dBError.dBError("E067")

        if eventName not in self.__functionNames:
            raise dBError.dBError("E066")

        self.__dispatch.bind(eventName, callback)

    def unbind(self, eventName, callback):
        if eventName not in self.__functionNames:
            return
        self.__dispatch.unbind(eventName, callback)

    def unbind(self, eventName):
        if eventName not in self.__functionNames:
            return
        self.__dispatch.unbind(eventName, None)

    async def handle_dispatcher(self, functionName, returnSubect, sid, payload):
        try:
            response = cfrpcResponse.responseHandler(functionName, returnSubect, sid, self.__dbcore, cfrpcResponse.HandlerTypes.CF)
            await self.__dispatch.emit_cf(functionName, payload, response)
        except Exception as e:
            pass

    async def handle_tracker_dispatcher(self, responseid, errorcode):
        await self.__dispatch.emit_cf('cf.response.tracker', responseid, errorcode)

    async def handle_exceed_dispatcher(self):
        err = dBError.dBError("E070")
        err.updateCode("CALLEE_QUEUE_EXCEEDED")
        await self.__dispatch.emit_cf('cf.callee.queue.exceeded', err, None)

    async def handle_callResponse(self, sid, payload, isend, rsub):
        if sid in self.__sid_functionname:
            metadate = {"functionName": self.__sid_functionname[sid]}
            await self.__dispatch.emit_clientfunction2(sid, payload, isend,rsub)



    async def resetqueue(self):
        m_status  = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.CF_CALLEE_QUEUE_EXCEEDED, None, None, None, None, None, None, None)
        if not m_status:
            raise dBError.dBError("E068")
            