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
import multiprocessing
import threading

import traceback

import aiohttp
import socketio
from .connections import connection
from .events import dBConnectionEvents

from .stations import station , channelState
from .messageTypes import dBTypes

from .dispatchers import dispatcher

from .clientFunctions import clientFunction

from .exceptions import dBError
from .remoteProcedure import rpc

from .remoteProcedure import rpcState

from .commonUtils import aioTimer
import math

import requests
import random
import urllib3
import json
import time
from urllib.parse import urlencode

urllib3.disable_warnings()


class dBridges:
    def __init__(self):
        self.auth_url = None
        self.__ClientSocket = None
        self.sessionid = None

        self.appkey = None

        self.connectionstate = connection.connectStates(self)
        self.channel = station.channels(self)
        self.__options = {}

        self.maxReconnectionRetries = 10
        self.maxReconnectionDelay = 120
        self.minReconnectionDelay = 1 + random.randint(0, 1) * 4
        self.reconnectionDelayGrowFactor = 1.3
        self.minUptime = 0.5
        self.connectionTimeout = 10
        self.autoReconnect = True


        self.__uptimeTimeout = None
        self.__retryCount = 0

        self.__lifeCycle = 0
        self.__isServerReconnect = False
        self.__dispatch = dispatcher.dispatcher()
        self.cf = clientFunction.cfclient(self)
        self.__disconnectedBy = ""
        self.rpc = rpc.CRpc(self)
        self.__metadata = {"channelname": None, "eventname": None, "sourcesysid": None,
                           "sqnum": None, "sessionid": None, "intime": None,
                           }

    def access_token(self, callback):
        if not callback:
            raise dBError.dBError("E004")

        if not callable(callback):
            raise dBError.dBError("E004")
        if not self.__dispatch.isExists("dbridges:access_token"):
            self.__dispatch.bind("dbridges:access_token", callback)
        else:
            raise dBError.dBError("E004")

    async def accesstoken_dispatcher(self, channelName, action, response):
        if self.__dispatch.isExists("dbridges:access_token"):
            await self.__dispatch.emit2("dbridges:access_token", channelName, self.sessionid, action, response)
        else:
            raise dBError.dBError("E004")

    async def __acceptOpen(self):
        self.__retryCount = 0
        self.connectionstate.reconnect_attempt = self.__retryCount

        if self.__lifeCycle == 0:
            await self.connectionstate.handledispatcher(dBConnectionEvents.states.CONNECTED)
            self.__lifeCycle += 1
        else:
            await self.connectionstate.handledispatcher(dBConnectionEvents.states.RECONNECTED)

    def __getNextDelay(self):
        delay = 0
        if self.__retryCount > 0:
            delay = self.minReconnectionDelay * math.pow(self.reconnectionDelayGrowFactor, self.__retryCount - 1)
            if delay > self.maxReconnectionDelay:
                delay = self.maxReconnectionDelay

            if delay < self.minReconnectionDelay:
                delay = self.minReconnectionDelay

        return delay

    def __wait(self):
        time.sleep(self.__getNextDelay())

    async def __reconnect(self):
        try:
            if self.__retryCount >= self.maxReconnectionRetries:
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.RECONNECT_FAILED, dBError.dBError("E060"))
                if self.__ClientSocket:
                    self.__ClientSocket = None

                self.__lifeCycle = 0
                self.__retryCount = 0
                self.connectionstate.set_newLifeCycle(True)
                await self.channel.cleanUp_All()
                await self.rpc.cleanUp_All()
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.DISCONNECTED, None)
            else:
                self.__retryCount += 1
                self.__wait()
                self.connectionstate.reconnect_attempt = self.__retryCount
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.RECONNECTING, None)
                await self.connect()
        except Exception as e:
            pass

    async def shouldRestart(self, eventdata):
        try:
            if self.autoReconnect:
                if not self.connectionstate.get_newLifeCycle():
                    if type(eventdata) == str:
                        await self.connectionstate.handledispatcher(dBConnectionEvents.states.RECONNECT_ERROR, dBError.dBError(eventdata))
                    else:
                        await self.connectionstate.handledispatcher(dBConnectionEvents.states.RECONNECT_ERROR, eventdata)
                    await self.__reconnect()
                    return
                else:
                    if type(eventdata) == str:
                        await self.connectionstate.handledispatcher(dBConnectionEvents.states.ERROR, dBError.dBError(eventdata))
                    else:
                        await self.connectionstate.handledispatcher(dBConnectionEvents.states.ERROR, eventdata)
                    return
        except Exception as e:
            pass

    async def disconnect(self):
       
        self.__disconnectedBy = "io client disconnect"
        await self.__ClientSocket.disconnect()


    async def connect(self):

        if self.__retryCount == 0 and not self.connectionstate.get_newLifeCycle():
            self.connectionstate.set_newLifeCycle(True)

        if not self.auth_url:
            if self.connectionstate.get_newLifeCycle():
                raise dBError.dBError("E001")
            else:
                await self.shouldRestart(dBError.dBError("E001"))
                return

        if not self.appkey:
            if self.connectionstate.get_newLifeCycle():
                raise dBError.dBError("E002")
            else:
                await self.shouldRestart(dBError.dBError("E002"))
                return


        try:
            self.cf.verify_function()
        except dBError.dBError as e:
            if self.connectionstate.get_newLifeCycle():
                raise e
            else:
                await self.shouldRestart(e)
                return

        jdata = None
        try:
            jdata = await self.GetdBRInfo2(self.auth_url, self.appkey)
        except dBError.dBError as e:
            if self.connectionstate.get_newLifeCycle():
                raise e
            else:
                await self.shouldRestart(e)


        if not jdata:
            db = dBError.dBError("E008")
            await self.shouldRestart(db)
            return

        secure = jdata["secured"]
        if secure:
            protocol = "https://"
        else:
            protocol = "http://"
        dbripport = protocol + jdata["wsip"] + ":" + jdata["wsport"]
        self.__options['query'] = {
            'sessionkey': jdata["sessionkey"],
            'version': '1.1',
            'libtype': 'python',
            'cf': self.cf.enable}

        if "secure" not in self.__options:
            self.__options["secure"] = True
        else:
            self.__options["secure"] = True

        if "rejectUnauthorized" not in self.__options:
            self.__options["rejectUnauthorized"] = False
        else:
            self.__options["rejectUnauthorized"] = False

        if "retryInterval" not in self.__options:
            self.__options["retryInterval"] = 5
        else:
            self.__options["retryInterval"] = 5

        if "retryAttempt" not in self.__options:
            self.__options["retryAttempt"] = 0
        else:
            self.__options["retryAttempt"] = 0

        if "reconnect" not in self.__options:
            self.__options["reconnect"] = False
        else:
            self.__options["reconnect"] = False

        self.__options['transports'] = ['websocket']

        if self.connectionTimeout <= 0:
            self.__options["timeout"] = 20000
        else:
            self.__options["timeout"] = self.connectionTimeout

        if self.__lifeCycle == 0:
            await self.connectionstate.handledispatcher(dBConnectionEvents.states.CONNECTING, {})



        self.connectionstate.set_newLifeCycle(True)

        self.__ClientSocket = socketio.AsyncClient(ssl_verify=False , reconnection=self.__options["reconnect"])

        self.__ClientSocket.on("disconnect", self.disconnected)
        self.__ClientSocket.on("connect_error", self.connect_error)
        self.__ClientSocket.on("connect_failed", self.connect_failed)
        self.__ClientSocket.on("db", self.IOMessage)
        try:
            self.__isServerReconnect = False
            self.__disconnectedBy = ""
            qstr = urlencode(self.__options['query'])
            await asyncio.sleep(0.0001)
            await self.__ClientSocket.connect(dbripport + '/?' + qstr, transports=['websocket'])
            await self.__ClientSocket.wait()
        except Exception as e:
            raise e


    async def GetdBRInfo2(self, auth_url , appkey ):
        try:
            iheaders = {"Content-Type": "application/json",
                        "x-api-key": appkey,
                        "lib-transport": "sio",
                        "User-Agent": "Mozilla/5.0"
                        }
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                r = await session.post(auth_url, data="{}", headers=iheaders)

                if r.status != 200:
                    dberror = dBError.dBError("E006")
                    dberror.updateCode(r.status, r.reason)
                    raise dberror

                if r.status == 200:
                    rdata = await r.text()
                    resultoutput = json.loads(rdata)

                    return resultoutput
        except dBError.dBError as e:
            raise e
        except Exception as e:
            dberror = dBError.dBError("E008")
            ecode = "NA"
            ereason = ""
            if hasattr(e, 'code'):
                ecode = e.code

            if hasattr(e ,  "reason"):
                ereason = e.reason
            else:
                ereason =  str(e)
            dberror.updateCode(ecode, ereason)
            raise dberror



    async def disconnected(self):
        try:
           
            await self.__IOEventReconnect(self.__disconnectedBy)
            
        except Exception as e:
            pass


    async def __IOEventReconnect(self, reason):
        if self.connectionstate.state == "":
            return 
       
        await self.channel.send_OfflineEvents()
        await self.rpc.send_OfflineEvents()
        
        if reason == "io server disconnect":
            if self.__ClientSocket:
                self.__ClientSocket = None
                
            if not self.autoReconnect:
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.ERROR, dBError.dBError("E061"))

                self.__lifeCycle = 0
                self.__retryCount = 0
                self.connectionstate.set_newLifeCycle(True)
                await self.channel.cleanUp_All()
                await  self.rpc.cleanUp_All()
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.DISCONNECTED, None);

            else:
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.CONNECTION_BREAK,
                                                            dBError.dBError("E062"))
                self.__disconnectedBy = ""
                await self.__reconnect()
            
            return

        if reason == "io client disconnect":
            if self.__ClientSocket:
                self.__ClientSocket = None

            self.__lifeCycle = 0
            self.__retryCount = 0
            self.connectionstate.set_newLifeCycle(True)
            await self.channel.cleanUp_All()
            await  self.rpc.cleanUp_All()
            await self.connectionstate.handledispatcher(dBConnectionEvents.states.DISCONNECTED, None)
            
                
        else:

            if reason != "io server disconnect" and reason != "io client disconnect":
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.CONNECTION_BREAK,
                                                        dBError.dBError("E063"))
            if self.__ClientSocket:
                self.__ClientSocket = None
            if not self.autoReconnect:
                
                self.__lifeCycle = 0
                self.__retryCount = 0
                self.connectionstate.set_newLifeCycle(True)
                await self.channel.cleanUp_All()
                await  self.rpc.cleanUp_All()    
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.DISCONNECTED, None);
            else:
                await self.__reconnect()



    def connect_error(self, data):
        try:
            self.__disconnectedBy = data
            self.__ClientSocket.start_background_task(self.__IOError, data)
        except Exception as e:
            pass


    async def __IOError(self, err):
        try:
            await self.connectionstate.handledispatcher(dBConnectionEvents.states.ERROR, err)
            if self.autoReconnect:
                if self.__ClientSocket:
                    self.__ClientSocket = None
                await self.__reconnect()
        except Exception as e:
            pass


    def isSocketConnected(self):
        if self.__ClientSocket:
            return self.__ClientSocket.connected
        else:
            return False

    async def send(self, msgDbp):
        flag = False
        try:
            
            await self.__ClientSocket.emit("db", (msgDbp["dbmsgtype"],
                                                    msgDbp["subject"],msgDbp["rsub"], msgDbp["sid"],
                                                    msgDbp["payload"], msgDbp["fenceid"], msgDbp["rspend"],
                                                    msgDbp["rtrack"], msgDbp["rtrackstat"], msgDbp["t1"],
                                                    msgDbp["latency"], msgDbp["globmatch"], msgDbp["sourceid"],
                                                        msgDbp["sourceip"],msgDbp["replylatency"], msgDbp["oqueumonitorid"]))
            return True
        except Exception as e:
            print(e)
            return False

    async def connect_failed(self, info):
        await self.connectionstate.handledispatcher(dBConnectionEvents.states.ERROR, None)
        if self.autoReconnect:
            await self.__reconnect()

    def ExecuteAsyncOperation(self, functionName, margs):
        try:
            p = multiprocessing.Process(target=functionName, args=margs)
            p.daemon = True
            p.start()
            return p
        except Exception as e:
            pass

    def ExecuteThreadOperation(self,  functionName ,  margs):
        try:
            t1 = threading.Thread(target=functionName , args=margs)
            t1.daemon = True
            t1.start()
            return t1
        except Exception as e:
            pass

    def IOMessage(self, *args):
        dbmsgtype = args[0]
        subject = args[1]
        rsub = args[2]
        sid = args[3]
        p_payload = args[4]
        fenceid = args[5]
        rspend = args[6]
        rtrack = args[5]
        rtrackstat = args[8]
        t1 = args[9]
        latency = args[10]
        globmatch = args[11]
        sourceid = args[12]
        sourceip = args[13]
        replylatency = args[14]
        oqueumonitorid = args[15]

        try:
            task = self.__ClientSocket.start_background_task(self.__IOMessage ,  dbmsgtype, subject,
                                                            rsub, sid, p_payload, fenceid, rspend,
                                                            rtrack, rtrackstat, t1,latency, globmatch,
                                                            sourceid, sourceip, replylatency,
                                                            oqueumonitorid)


        except Exception as e:
            pass

    async def ReplyLatency(self, recdlatency, oqueumonitorid):
        if (self.__ClientSocket.connected):

            await self.__ClientSocket.emit('db', dBTypes.messageType.LATENCY, None, None, None, None, None, None,
                                     None, None, None, recdlatency, None, None, None, True, oqueumonitorid)

    async def Rttpong(self, dbmsgtype, subject, rsub, sid, payload, fenceid,
                rspend, rtrack, rtrackstat, t1, latency, globmatch,
                sourceid, sourceip, replylatency, oqueumonitorid):

        try:
           await self.__ClientSocket.emit('db', (dbmsgtype, subject, rsub, sid, payload, fenceid,
                                 rspend, rtrack, rtrackstat, t1, latency, globmatch,sourceid, sourceip,
                                                                          replylatency, oqueumonitorid))

        except Exception as e:
            pass

    async def __IOMessage(self, dbmsgtype, subject, rsub, sid, payload, fenceid, rspend, rtrack, rtrackstat, t1, latency,
                    globmatch, sourceid, sourceip, replylatency, oqueumonitorid):

        mchannelName = None
        metadata = None

        recieved = round(time.time())

        recdDate = 0
        if t1:
            recdDate = t1

        lib_latency = recieved - recdDate
        caller = None
        dberr = None
        rpccaller = None
        extradata = None

        if dbmsgtype == dBTypes.messageType.SYSTEM_MSG.value:
            if subject == "connection:success":
                self.sessionid = str(payload, 'utf-8')
                if self.connectionstate.get_newLifeCycle():
                    if self.cf.enable:
                        if asyncio.iscoroutinefunction(self.cf.functions):
                            await self.cf.functions()
                        else:
                            self.cf.functions()
                self.connectionstate.set_newLifeCycle(False)
                if self.minUptime < 0:
                    waittime = 5
                else:
                    waittime = self.minUptime

                await self.rpc.ReSubscribeAll()
                await self.channel.ReSubscribeAll()

                r = aioTimer.Timer(waittime, self.__acceptOpen)
                await r.wait()

                if t1:
                    await self.Rttpong(dbmsgtype, "rttpong", rsub, sid, payload, fenceid,
                                                              rspend, rtrack, rtrackstat, t1, lib_latency, globmatch,
                                                              sourceid, sourceip, replylatency, oqueumonitorid)

            if subject == "rttping":
                if t1:
                    await self.Rttpong(dbmsgtype, "rttpong", rsub, sid, payload, fenceid,
                                 rspend, rtrack, rtrackstat, t1, lib_latency, globmatch,
                                 sourceid, sourceip, replylatency, oqueumonitorid)
            if subject == "rttpong":
                if t1:

                    eventData = (time.time()*1000) / 1000 -  t1

                    self.connectionstate.rttms = round(eventData*1000)
                    await self.connectionstate.handledispatcher(dBConnectionEvents.states.RTTPONG, eventData)

            if subject == "reconnect":
                self.__isServerReconnect = True
                self.__disconnectedBy = "io server disconnect"
                await self.__ClientSocket.disconnect()

            if subject not in ["reconnect","rttpong", "rttping", "connection:success" ]:
                dberr = dBError.dBError("E082")
                dberr.updateCode(subject, payload.decode("utf-8") )
                await self.connectionstate.handledispatcher(dBConnectionEvents.states.ERROR, dberr)
            pass

        if dbmsgtype == dBTypes.messageType.SUBSCRIBE_TO_CHANNEL.value:
            sidStatus = self.channel.get_subscribeStatus(sid)
            if subject == "success":
                if sidStatus == channelState.states.SUBSCRIPTION_INITIATED:
                    await self.channel.updateChannelsStatusAddChange(0, sid,
                                                               channelState.states.SUBSCRIPTION_ACCEPTED, "")
                if sidStatus == channelState.states.SUBSCRIPTION_ACCEPTED or sidStatus == channelState.states.SUBSCRIPTION_PENDING:
                    await self.channel.updateChannelsStatusAddChange(1, sid,
                                                               channelState.states.SUBSCRIPTION_ACCEPTED, "")
            else:
                dberr = dBError.dBError("E064")
                dberr.updateCode(str(subject).upper(), str(payload))

                if sidStatus == channelState.states.SUBSCRIPTION_INITIATED:
                    await self.channel.updateChannelsStatusAddChange(0, sid, channelState.states.SUBSCRIPTION_ERRORs,
                                                               dberr)
                    if sidStatus == channelState.states.SUBSCRIPTION_ACCEPTED or sidStatus == channelState.states.SUBSCRIPTION_PENDING:
                        await self.channel.updateChannelsStatusAddChange(1, sid,
                                                                   channelState.states.SUBSCRIPTION_PENDING, dberr)

        if dbmsgtype == dBTypes.messageType.CONNECT_TO_CHANNEL.value:
            sidStatus = self.channel.get_subscribeStatus(sid)
            if subject == "success":
                if sidStatus == channelState.states.CONNECTION_INITIATED:
                    await self.channel.updateChannelsStatusAddChange(0, sid,
                                                                     channelState.states.CONNECTION_ACCEPTED, "")
                if sidStatus == channelState.states.CONNECTION_ACCEPTED or sidStatus == channelState.states.CONNECTION_PENDING:
                    await self.channel.updateChannelsStatusAddChange(1, sid,
                                                                     channelState.states.CONNECTION_ACCEPTED, "")
            else:
                dberr = dBError.dBError("E084")
                if payload:
                    dberr.updateCode(str(subject).upper(), str(payload))
                else:
                    dberr.updateCode(str(subject).upper(), "")

                if sidStatus == channelState.states.CONNECTION_INITIATED:
                    await self.channel.updateChannelsStatusAddChange(0, sid, channelState.states.CONNECTION_ERROR,
                                                                     dberr)
                    if sidStatus == channelState.states.CONNECTION_INITIATED or sidStatus == channelState.states.CONNECTION_ACCEPTED:
                        await self.channel.updateChannelsStatusAddChange(1, sid,
                                                                         channelState.states.CONNECTION_PENDING,
                                                                         dberr)
        if dbmsgtype == dBTypes.messageType.UNSUBSCRIBE_DISCONNECT_FROM_CHANNEL.value:
            sidtype = self.channel.get_channelType(sid)
            if subject == "success":
                if sidtype == "s":
                    await self.channel.updateChannelsStatusRemove(sid, channelState.states.UNSUBSCRIBE_ACCEPTED, "")
                else:
                    await self.channel.updateChannelsStatusRemove(sid, channelState.states.DISCONNECT_ACCEPTED, "")
            else:
                if sidtype == "s":
                    dberr = dBError.dBError("E065")
                    if payload:
                        dberr.updateCode(str(subject).upper(), str(payload))
                    else:
                        dberr.updateCode(str(subject).upper(), "")

                    await self.channel.updateChannelsStatusRemove(sid, channelState.states.UNSUBSCRIBE_ERROR, "")
                else:
                    dberr = dBError.dBError("E088")
                    if payload:
                        dberr.updateCode(str(subject).upper(), str(payload))
                    else:
                        dberr.updateCode(str(subject).upper(), "")
                    await self.channel.updateChannelsStatusRemove(sid, channelState.states.DISCONNECT_ERROR, "")

        if dbmsgtype == dBTypes.messageType.PUBLISH_TO_CHANNEL.value:
            mchannelName = self.channel.get_channelName(sid)
            metadata =self.__metadata
            metadata["eventname"] = subject
            metadata["sourcesysid"] = sourceid
            metadata["sessionid"] = sourceip
            metadata["sqnum"] = oqueumonitorid
            if t1:
                metadata["intime"] = t1

            if  str(mchannelName).lower().startswith("sys:*"):
                metadata["channelname"] = fenceid
            else:
                metadata["channelname"] = mchannelName
            mpayload = ""
            try:
                if payload:
                    mpayload = str(payload, 'utf-8')
            except Exception as e:
                mpayload = ""

            await self.channel.handledispatcherEvents(subject, mpayload, mchannelName, metadata)

        if dbmsgtype == dBTypes.messageType.PARTICIPANT_JOIN.value:
            mchannelName = self.channel.get_channelName(sid)
            metadata = self.__metadata
            metadata["eventname"] = 'dbridges:participant.joined'
            metadata["sourcesysid"] = sourceid
            metadata["sessionid"] = sourceip
            metadata["sqnum"] = oqueumonitorid
            metadata["channelname"] = mchannelName

            if str(mchannelName).lower().startswith("sys:") or str(mchannelName).lower().startswith("prs:"):

                if str(mchannelName).lower().startswith("sys::*"):
                    cresult = self.convertToObject(sourceip, sourceid, fenceid)
                    metadata["sessionid"] =  cresult["s"]
                    metadata["sourcesysid"] = cresult["sysid"]
                    await self.channel.handledispatcherEvents('dbridges:participant.joined',cresult["i"] , mchannelName, metadata)
                else:
                    cresult = self.convertToObject(sourceip, sourceid)
                    metadata["sessionid"] = cresult["s"]
                    metadata["sourcesysid"] = cresult["sysid"]
                    await self.channel.handledispatcherEvents('dbridges:participant.joined', cresult["i"], mchannelName, metadata)
            else:
                await self.channel.handledispatcherEvents('dbridges:participant.joined', {"sourcesysid":sourceid}, mchannelName, metadata)

        if dbmsgtype == dBTypes.messageType.PARTICIPANT_LEFT.value:
            mchannelName = self.channel.get_channelName(sid)
            metadata = self.__metadata
            metadata["eventname"] = 'dbridges:participant.left'
            metadata["sourcesysid"] = sourceid
            metadata["sessionid"] = sourceip
            metadata["sqnum"] = oqueumonitorid
            metadata["channelname"] = mchannelName

            if str(mchannelName).lower().startswith("sys:") or str(mchannelName).lower().startswith("prs:"):
                if str(mchannelName).lower().startswith("sys::*"):
                    cresult = self.convertToObject(sourceip, sourceid, fenceid)
                    metadata["sessionid"] = cresult["s"]
                    metadata["sourcesysid"] = cresult["sysid"]
                    await self.channel.handledispatcherEvents('dbridges:participant.left',
                                                        cresult["i"], mchannelName,
                                                        metadata)
                else:
                    cresult = self.convertToObject(sourceip, sourceid)
                    metadata["sessionid"] = cresult["s"]
                    metadata["sourcesysid"] = cresult["sysid"]
                    await self.channel.handledispatcherEvents('dbridges:participant.left',
                                                        cresult["i"], mchannelName,
                                                        metadata)
            else:
                await self.channel.handledispatcherEvents('dbridges:participant.left', {"sourcesysid": sourceid},
                                                    mchannelName, metadata)

        if dbmsgtype == dBTypes.messageType.CF_CALL_RECEIVED.value:
            mpayload = None
            try:
                if payload:
                    mpayload = str(payload, 'utf-8')
                else:
                    mpayload = ""
            except Exception as e:
                mpayload = ""
            try:
                await self.cf.handle_dispatcher(subject, rsub, sid, mpayload)
            except Exception as e:
                pass

        if dbmsgtype == dBTypes.messageType.CF_CALL_RESPONSE.value:
            mpayload = None
            try:
                if payload:
                    mpayload = str(payload, 'utf-8')
                else:
                    mpayload = ""
            except Exception as e:
                mpayload = ""
            try:
                await self.cf.handle_callResponse(sid, mpayload, rspend, rsub)
            except Exception as e:
                pass

        if dbmsgtype == dBTypes.messageType.CF_RESPONSE_TRACKER.value:
            await self.cf.handle_tracker_dispatcher(subject, rsub)

        if dbmsgtype == dBTypes.messageType.CF_CALLEE_QUEUE_EXCEEDED.value:
            await self.cf.handle_exceed_dispatcher()

        if dbmsgtype == dBTypes.messageType.CONNECT_TO_RPC_SERVER.value:
            sidStatus = self.rpc.get_rpcStatus(sid)
            if subject == "success":
                if sidStatus == rpcState.states.RPC_CONNECTION_INITIATED:
                    await self.rpc.updateRegistrationStatusAddChange(0, sid, rpcState.states.RPC_CONNECTION_ACCEPTED,
                                                               "")
                if sidStatus == rpcState.states.RPC_CONNECTION_ACCEPTED or \
                        sidStatus == rpcState.states.RPC_CONNECTION_PENDING:
                    await self.rpc.updateRegistrationStatusAddChange(1, sid, rpcState.states.RPC_CONNECTION_ACCEPTED,
                                                               "")
            else:
                dberr = dBError.dBError("E082")
                if payload:
                    dberr.updateCode(str(subject).upper(), str(payload))
                else:
                    dberr.updateCode(str(subject).upper(), "")

                if sidStatus == rpcState.states.RPC_CONNECTION_INITIATED:
                    await self.rpc.updateRegistrationStatusAddChange(0, sid, rpcState.states.RPC_CONNECTION_ERROR,
                                                               dberr)

                if sidStatus == rpcState.states.RPC_CONNECTION_ACCEPTED or \
                        sidStatus == rpcState.states.RPC_CONNECTION_PENDING:
                    await self.rpc.updateRegistrationStatusAddChange(1, sid, rpcState.states.RPC_CONNECTION_PENDING,
                                                               dberr)


        if dbmsgtype == dBTypes.messageType.RPC_CALL_RECEIVED.value:
            mpayload = None
            if int(sid) > 0:
                try:
                    if payload:
                        mpayload = str(payload, 'utf-8')
                    else:
                        mpayload = ""
                except Exception as e:
                    mpayload = ""
                rpccaller = self.rpc.get_object(sid)
                if rpccaller:
                    await rpccaller.handle_callResponse(sid, mpayload, rspend, rsub)
                else:
                    rpccaller = self.rpc.get_rpcServerObject(sid)
                    if rpccaller:
                        await rpccaller.handle_dispatcher_WithObject(subject, rsub, sid, mpayload, sourceip, sourceid)


        if dbmsgtype == dBTypes.messageType.RPC_CALL_RESPONSE.value:
            mpayload = None
            if int(sid) > 0:
                try:
                    if payload:
                        mpayload = str(payload, 'utf-8')
                    else:
                        mpayload = ""
                except Exception as e:
                    mpayload = ""
                rpccaller = self.rpc.get_object(sid)
                if rpccaller:
                    await rpccaller.handle_callResponse(sid, mpayload, rspend, rsub)
                else:
                    rpccaller = self.rpc.get_rpcServerObject(sid)
                    if rpccaller:
                        await rpccaller.handle_dispatcher_WithObject(subject, rsub, sid, mpayload, sourceip, sourceid)

        if dbmsgtype == dBTypes.messageType.RPC_RESPONSE_TRACKER.value:
            rpccaller = self.rpc.get_rpcServerObject(sid)
            await rpccaller.handle_tracker_dispatcher(subject, rsub)

        if dbmsgtype == dBTypes.messageType.RPC_CALLEE_QUEUE_EXCEEDED.value:
            rpccaller = self.rpc.get_rpcServerObject(sid)
            await rpccaller.handle_exceed_dispatcher()

        if dbmsgtype == dBTypes.messageType.REGISTER_RPC_SERVER.value:
            sidStatus = self.rpc.get_rpcStatus(sid)
            if subject == "success":
                if sidStatus == rpcState.states.REGISTRATION_INITIATED:
                    await self.rpc.updateRegistrationStatusAddChange(0, sid, rpcState.states.REGISTRATION_ACCEPTED,
                                                               "")
                if sidStatus == rpcState.states.REGISTRATION_ACCEPTED or \
                        sidStatus == rpcState.states.REGISTRATION_PENDING:
                    await self.rpc.updateRegistrationStatusAddChange(1, sid, rpcState.states.REGISTRATION_ACCEPTED,
                                                               "")
            else:
                dberr = dBError.dBError("E081")
                if payload:
                    dberr.updateCode(str(subject).upper(), payload)
                else:
                    dberr.updateCode(str(subject).upper(), "")

                if sidStatus == rpcState.states.REGISTRATION_INITIATED:
                    await self.rpc.updateRegistrationStatusAddChange(0, sid, rpcState.states.REGISTRATION_ERROR,
                                                               dberr)

                if sidStatus == rpcState.states.REGISTRATION_ACCEPTED or \
                        sidStatus == rpcState.states.REGISTRATION_PENDING:
                    await self.rpc.updateRegistrationStatusAddChange(1, sid, rpcState.states.REGISTRATION_PENDING,
                                                               dberr)

    def convertToObject(self, sourceip, sourceid, channelname=None):
        sessionid = ""
        libtype = ""
        sourceipv4 = ""
        sourceipv6 = ""
        msourceid = ""
        sourcesysid = ""
        if sourceid:
            strData = sourceid.split("#")
            ilength =  len(strData)
            if ilength > 0:
                sessionid = strData[0]
            if ilength > 1:
                libtype = strData[1]
            if ilength > 2:
                sourceipv4 = strData[2]
            if ilength >= 3:
                sourceipv6 = strData[3]
            if ilength >= 4:
                sourcesysid = strData[4]

        if channelname:
            inObject = {
                "sessionid": sessionid, "libtype": libtype,
                "sourceipv4": sourceipv4, "sourceipv6": sourceipv6, "sysinfo": sourceip,
                "channelname": channelname, "sourcesysid": sourcesysid
            }
        else:
            inObject = {
                "sessionid": sessionid, "libtype": libtype,
                "sourceipv4": sourceipv4, "sourceipv6": sourceipv6, "sysinfo": sourceip, "sourcesysid": sourcesysid
            }
        return {"i": inObject, "s": sessionid, "sysid": sourcesysid}
