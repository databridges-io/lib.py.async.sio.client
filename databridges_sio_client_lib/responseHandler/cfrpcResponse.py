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
import json
from ..messageTypes import dBTypes
from ..commonUtils import util

from ..exceptions import dBError
from enum import Enum
class HandlerTypes(Enum):
    CF = "cf"
    RPC = "rpc"

class responseHandler:
    def __init__(self, functionName, returnSubect, sid, dbcoreobject, mtypes):
        self.__functionName = functionName
        self.__returnSubsect = returnSubect
        self.__sid = sid
        self.__dbcore = dbcoreobject
        self.__isend = False
        self.id = returnSubect
        self.tracker = False
        self.__m_type = mtypes

    async def next(self, data):
        cstatus = None

        if not self.__isend:
            if self.__m_type == HandlerTypes.RPC:
                cstatus = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.RPC_CALL_RESPONSE,None,
                                                  self.__returnSubsect,None, self.__sid, data, self.__isend, self.tracker)
            else:
                cstatus = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.CF_CALL_RESPONSE, None,
                                                  self.__returnSubsect,None, self.__sid, data, self.__isend, self.tracker)

            if (not cstatus):
                if self.__m_type == HandlerTypes.RPC:
                    raise dBError.dBError("E079")
                else:
                    raise dBError.dBError("E068")
        else:
            if self.__m_type == HandlerTypes.RPC:
                raise dBError.dBError("E106")
            else:
                raise dBError.dBError("E105")

    async def end(self, data):
        if not self.__isend:
            self.__isend = True
            if self.__m_type == HandlerTypes.RPC:
                cstatus = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.RPC_CALL_RESPONSE,None,
                                                  self.__returnSubsect, None, self.__sid, data, self.__isend,
                                                  self.tracker)
            else:
                cstatus = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.CF_CALL_RESPONSE,
                                                    None, self.__returnSubsect, None, self.__sid, data, self.__isend,
                                                  self.tracker)

            if (not cstatus):
                if self.__m_type == HandlerTypes.RPC:
                    raise dBError.dBError("E079")
                else:
                    raise dBError.dBError("E068")
        else:
            if self.__m_type == HandlerTypes.RPC:
                raise dBError.dBError(
                    "E106")
            else:
                raise dBError.dBError("E105")

    async def exception(self, expCode, expShortMessage):
        epayload = json.dumps({'c': expCode, 'm': expShortMessage})
        if not self.__isend:
            self.__isend = True

            if self.__m_type == HandlerTypes.RPC:
                cstatus = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.RPC_CALL_RESPONSE, None,
                                                  self.__returnSubsect, "EXP", self.__sid, epayload, self.__isend,
                                                  self.tracker)
            else:
                cstatus = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.CF_CALL_RESPONSE,None,
                                                  self.__returnSubsect, "EXP", self.__sid, epayload, self.__isend,
                                                  self.tracker)

            if (not cstatus):
                if self.__m_type == HandlerTypes.RPC:
                    raise dBError.dBError("E079")
                else:
                    raise dBError.dBError("E068")
        else:
            if self.__m_type == HandlerTypes.RPC:
                raise dBError.dBError(
                    "E106")
            else:
                raise dBError.dBError("E105")
