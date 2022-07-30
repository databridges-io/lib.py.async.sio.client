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
import json
import random

from ..dispatchers import dispatcher

from ..commonUtils import util, aioTimer
from ..messageTypes import  dBTypes
from ..responseHandler import  cfrpcResponse
from ..exceptions import  dBError
from ..commonUtils import aioPromise


class CrpCaller:
    def __init__(self, serverName, dBCoreObject, rpccoreobject, callertype="rpc"):
        self.__dispatch = dispatcher.dispatcher()
        self.__dbcore = dBCoreObject
        self.__rpccore = rpccoreobject
        self.enable = False
        self.functions = None
        self.__sid_functionname = {}
        self.__serverName = serverName
        self.__isOnline = False
        self.__callerTYPE = callertype

    def getServerName(self):
        return self.__serverName

    def isOnline(self):
        return self.__isOnline

    def set_isOnline(self, value):
        self.__isOnline = value

    def bind(self, eventName , callback):
        if not (eventName and not eventName.isspace()):
            raise dBError.dBError("E076")
        if not callback and not callable(callback):
            raise dBError.dBError("E077")
        self.__dispatch.bind(eventName, callback)

    def unbind(self, eventName, callback):
        self.__dispatch.unbind(eventName, callback)

    async def handle_dispatcher(self, functionName, returnSubect, sid, payload):
        response = cfrpcResponse.responseHandler(functionName, returnSubect, sid, self.__dbcore, cfrpcResponse.HandlerTypes.RPC)
        await self.__dispatch.emit_clientfunction(functionName, payload, response)

    async def handle_callResponse(self, sid, payload, isend, rsub):
        if sid in self.__sid_functionname.keys():
            await self.__dispatch.emit_clientfunction2(sid, payload, isend, rsub)

    async def handle_tracker_dispatcher(self, responseid, errorcode):
        await self.__dispatch.emit_clientfunction('rpc.response.tracker', responseid, errorcode)

    async def handle_exceed_dispatcher(self):
        err = dBError.dBError("E054")
        err.updatecode("CALLEE_QUEUE_EXCEEDED")
        await self.__dispatch.emit_clientfunction('rpc.callee.queue.exceeded', err, None)

    def GetUniqueSid(self, sid):
        nsid = sid + util.GenerateUniqueId();
        if nsid in self.__sid_functionname:
            nsid = ("" + str(random.randint(0, 999999)))
        return nsid


    async def __call_internal(self, sessionid , functionName ,  inparameter, sid, progress_callback):

        async def internal_call(resolve,reject):

            internal_result =  False

            cstatus = None;
            if self.__callerTYPE== 'rpc':
                cstatus = await util.updatedBNewtworkCF(self.__dbcore, dBTypes.messageType.CALL_RPC_FUNCTION, sessionid, functionName , None , sid ,  inparameter,None, None )

            else:
                cstatus =  await util.updatedBNewtworkCF(self.__dbcore , dBTypes.messageType.CALL_CHANNEL_RPC_FUNCTION, sessionid, functionName , None , sid ,  inparameter,None, None );

            if not cstatus:
                if self.__callerTYPE == 'rpc':
                    reject( dBError.dBError("E079"))
                else:
                    reject(dBError.dBError("E033"))

            async def internal_response(response , rspend, rsub):
                nonlocal internal_result

                dberror = None
                if not rspend:

                    if progress_callback and callable(progress_callback):
                        if asyncio.iscoroutinefunction(progress_callback):
                            await progress_callback(response)
                        else:
                            progress_callback(response);
                else:

                    if rsub is not None:

                        ursub =  str(rsub).upper()
                        if ursub == "EXP":
                            eobject = json.loads(response)
                            if self.__callerTYPE == 'rpc':
                                dberror = dBError.dBError("E055")
                                dberror.updateCode(eobject["c"], eobject["m"] )
                                reject(dberror)
                                internal_result = True
                            else:
                                dberror = dBError.dBError("E041");
                                dberror.updateCode(eobject["c"], eobject["m"] );
                                reject(dberror)
                                internal_result = True
                        else:
                            if self.__callerTYPE == 'rpc':
                                dberror = dBError.dBError("E054")
                                dberror.updateCode(ursub, "" )
                                reject(dberror)
                            else:
                                dberror = dBError.dBError("E040")
                                dberror.updateCode(ursub , "")
                                reject(dberror)
                                internal_result = True
                    else:
                        resolve(response)
                        internal_result =  True

                    self.unbind(sid,None);
                    del self.__sid_functionname[sid]
            self.bind(sid ,  internal_response)
            while not internal_result:
                await asyncio.sleep(1)

        p = aioPromise.Promise()
        await p.Execute(internal_call)
        return p



    async def call(self, functionName ,  inparameter ,  ttlms , progress_callback):
        loop_index = 0
        loop_counter = 3
        mflag = False
        sid_created = True

        sid = util.GenerateUniqueId()
        while loop_index < loop_counter and not mflag:
            if sid in self.__sid_functionname:
                sid =  self.GetUniqueSid(sid)
                loop_index = loop_index + 1
            else:
                self.__sid_functionname[sid] = functionName
                mflag = True

        if not mflag:
            sid =  ("" + str(random.randint(0, 999999)))
            if not sid in self.__sid_functionname:
                self.__sid_functionname[sid] = functionName
            else:
                sid_created = False



        if not sid_created:
            if self.__callerTYPE == "rpc":
                raise dBError.dBError("E108")
            else:
                raise  dBError.dBError("E109")
            return

        self.__rpccore.store_object(sid , self)
        async def _call(resolve , reject):

            async def timeexpire():
                self.unbind(sid);
                del self.__sid_functionname[sid]
                if self.__callerTYPE == "rpc":
                    reject(dBError.dBError("E080"))
                else:
                    reject(dBError.dBError("E042"))
                await util.updatedBNewtworkCF(
                    self.__dbcore , dBTypes.messageType.RPC_CALL_TIMEOUT, None,sid,None , None , None , None , None );

            if ttlms < 100:
                new_ttlms = ttlms / 1000
            else:
                new_ttlms = ttlms

            r = aioTimer.Timer(new_ttlms, timeexpire)

            def successResolve(value):
                r.cancel()
                resolve(value)

            def successReject(value):
                r.cancel()
                reject(value)


            p =await self.__call_internal(self.__serverName ,functionName , inparameter,sid ,  progress_callback)


            p.then( successResolve).catch( successReject)

        pr = aioPromise.Promise()
        await pr.Execute(_call)
        return pr

    async def emit(self, eventName, eventData, metadata):
        await self.__dispatch.emit_channel(eventName, eventData, metadata)

    async def emit_channel(self, eventName, eventData, metadata):
        await self.__dispatch.emit_channel(eventName, eventData, metadata)