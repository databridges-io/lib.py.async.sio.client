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
import re
import traceback

from ..Tokens import  dBToken
from ..messageTypes import dBTypes

from ..stations import subscribeChannel, channelState, connectChannel
from ..privateAccess import accessResponse

from ..events import dBEvents

from ..commonUtils import util, aioPromise
from ..dispatchers import dispatcher
from ..exceptions import dBError

class channels:
    def __init__(self, dBCoreObject):
        self.__channel_type = ["pvt", "prs", "sys"]
        self.__channelsid_registry = dict()
        self.__channelname_sid = dict()
        self.__dbcore = dBCoreObject
        self.__dispatch = dispatcher.dispatcher()
        self.__metadata = {"channelname": None, "eventname": None, "sourcesysid": None,
                           "sqnum": None, "sessionid": None, "intime": None}

    def bind(self, eventName, callback):
        self.__dispatch.bind(eventName, callback)

    def unbind(self, eventName, callback):
        self.__dispatch.unbind(eventName, callback)

    def bind_all(self, callback):
        self.__dispatch.bind_all(callback)

    def unbind_all(self, callback):
        self.__dispatch.unbind_all(callback)

    async def handledispatcher(self, eventName, eventInfo, metadata=None):
        await self.__dispatch.emit_channel(eventName, eventInfo, metadata)

    async def handledispatcherEvents(self, eventName, eventInfo=None, channelName=None, metadata=None):
        try:
            if channelName:
                await self.__dispatch.emit_channel(eventName, eventInfo, metadata)
                sid = self.__channelname_sid[channelName]
                m_object = self.__channelsid_registry[sid]
                if m_object:
                    await m_object["ino"].emit_channel(eventName, eventInfo, metadata)
        except Exception as e:
            pass

    def isPrivateChannel(self, channelName):
        flag = False
        if ":" in channelName:
            sdata = channelName.lower().split(":")
            if sdata[0] in self.__channel_type:
                flag = True
        return flag

    async def communicateR(self, mtype, channelName, sid, access_token):
        cStatus = False
        if mtype == 0:
            cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.SUBSCRIBE_TO_CHANNEL, channelName, sid,
                                              access_token)
        else:
            cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.CONNECT_TO_CHANNEL, channelName, sid,
                                              access_token)
        if not cStatus:
            if mtype == 0:
                raise dBError.dBError("E024")
            else:
                raise dBError.dBError("E090")

    async def _ReSubscribe(self, sid):
        m_object = self.__channelsid_registry[sid]
        access_token = None
        mprivate = self.isPrivateChannel(m_object["name"])
        if m_object["status"] == channelState.states.SUBSCRIPTION_ACCEPTED or m_object[
            "status"] == channelState.states.SUBSCRIPTION_INITIATED:
            try:
                if not mprivate:
                    await self.communicateR(0, m_object["name"], sid, access_token)
                else:
                    response = accessResponse.privateResponse(1,0, m_object["name"], sid, self)
                    await self.__dbcore.accesstoken_dispatcher(m_object["name"], dBToken.tokenTypes.CHANNELSUBSCRIBE.value,
                                                         response)

            except dBError.dBError as error:
                await self.handleSubscribeEvents([dBEvents.systemEvents.OFFLINE], error, m_object)
                return
        if m_object["status"] == channelState.states.CONNECTION_ACCEPTED or m_object[
            "status"] == channelState.states.CONNECTION_INITIATED:
            try:
                if not mprivate:
                    await self.communicateR(1, m_object["name"], sid, access_token)
                else:
                    response = accessResponse.privateResponse(1,1, m_object["name"], sid, self)
                    await self.__dbcore.accesstoken_dispatcher(m_object["name"], dBToken.tokenTypes.CHANNELCONNECT.value,
                                                         response)

            except dBError.dBError as error:
                await self.handleSubscribeEvents([dBEvents.systemEvents.OFFLINE], error, m_object)
                return


        if m_object["status"] == channelState.states.UNSUBSCRIBE_INITIATED:
            m_object["ino"].set_isOnline(False)
            await self.handleSubscribeEvents([dBEvents.systemEvents.UNSUBSCRIBE_SUCCESS, dBEvents.systemEvents.REMOVE], "",
                                       m_object)
            del self.__channelname_sid[m_object["name"]]
            del self.__channelsid_registry[sid]

        if m_object["status"] == channelState.states.DISCONNECT_INITIATED:
            m_object["ino"].set_isOnline(False)
            await self.handleSubscribeEvents([dBEvents.systemEvents.DISCONNECT_SUCCESS, dBEvents.systemEvents.REMOVE], "",
                                       m_object)
            del self.__channelname_sid[m_object["name"]]
            del self.__channelsid_registry[sid]


    async def ReSubscribeAll(self):
        for (k, v) in self.__channelname_sid.items():
            await self._ReSubscribe(v)

    def isEmptyOrSpaces(self, str):
        if str and str.strip():
            return False
        else:
            return True

    def validateChanelName(self, channelName, error_type=0):
        if not self.__dbcore.connectionstate.isconnected:
            if error_type == 0:
                raise dBError.dBError("E024")
            if error_type == 1:
                raise dBError.dBError("E090")
            if error_type == 2:
                raise dBError.dBError("E014")
            if error_type == 3:
                raise dBError.dBError("E019")
            if error_type == 4:
                raise dBError.dBError("E033")

        if type(channelName) is not str:
            if error_type == 0:
                raise dBError.dBError("E026")
            if error_type == 1:
                raise dBError.dBError("E095")
            if error_type == 2:
                raise dBError.dBError("E015")
            if error_type == 3:
                raise dBError.dBError("E020")
            if error_type == 4:
                raise dBError.dBError("E035")

        if self.isEmptyOrSpaces(channelName):
            if error_type == 0:
                raise dBError.dBError("E025")
            if error_type == 1:
                raise dBError.dBError("E095")
            if error_type == 2:
                raise dBError.dBError("E016")
            if error_type == 3:
                raise dBError.dBError("E021")
            if error_type == 4:
                raise dBError.dBError("E037")

        if len(channelName) > 64:
            if error_type == 0:
                raise dBError.dBError("E027")
            if error_type == 1:
                raise dBError.dBError("E095")
            if error_type == 2:
                raise dBError.dBError("E017")
            if error_type == 3:
                raise dBError.dBError("E022")
            if error_type == 4:
                raise dBError.dBError("E036")

        try:
            matchflag = re.match('^[a-zA-Z0-9\.:_-]*$', channelName)
        except Exception as e:
            matchflag = False

        if not matchflag:
            if error_type == 0:
                raise dBError.dBError("E028")
            if error_type == 1:
                raise dBError.dBError("E095")
            if error_type == 2:
                raise dBError.dBError("E015")
            if error_type == 3:
                raise dBError.dBError("E023")
            if error_type == 4:
                raise dBError.dBError("E039")

        if ":" in channelName:
            sdata = channelName.lower().split(":")
            if sdata[0] not in self.__channel_type:
                if error_type == 0:
                    raise dBError.dBError("E028")
                if error_type == 1:
                    raise dBError.dBError("E095")
                if error_type == 2:
                    raise dBError.dBError("E015")
                if error_type == 3:
                    raise dBError.dBError("E023")
                if error_type == 4:
                    raise dBError.dBError("E039")

    def verify_acccess_response(self, access_object):
        mresult = False
        merror = ""
        if "statuscode" not in access_object:
            merror = "the return object structure is blank, does not contain statuscode key"
            return {'result': False, 'msg': merror, 'token': ''}

        if not isinstance(access_object["statuscode"], int):
            merror = "the return object structure is blank, statuscode vaule must be numeric"
            return {'result': False, 'msg': merror, 'token': ''}

        if access_object["statuscode"] != 0:
            if "error_message" not in access_object:
                merror = "access_token function return statuscode: " + access_object.statuscode + " error_message tag missing"
            else:
                merror = access_object["error_message"]
            return {'result': False, 'msg': merror, 'token': ''}

        if "accesskey" not in access_object:
            merror = "access_token function return statuscode: " + access_object.statuscode + " accesskey tag missing"
            return {'result': False, 'msg': merror, 'token': ''}

        if not access_object["accesskey"]:
            merror = "access_token function return statuscode: " + access_object.statuscode + " accesskey is blank"
            return {'result': False, 'msg': merror, 'token': ''}

        return {'result': True, 'msg': '', 'token': access_object["accesskey"]}

    async def failure_dispatcher(self, mtype, sid, reason):
        m_object = self.__channelsid_registry[sid]
        m_object["ino"].set_isOnline(False)
        if mtype == 0:
            dberror = dBError.dBError("E091")
            dberror.updatecode("", reason)
            self.handleSubscribeEvents([util.systemEvents.SUBSCRIBE_FAIL], dberror, m_object)
        else:
            dberror = dBError.dBError("E092")
            dberror.updatecode("", reason)

            self.handleSubscribeEvents([util.systemEvents.CONNECT_FAIL], dberror, m_object)
        del self.__channelname_sid[m_object["name"]]
        del self.__channelsid_registry[sid]

    async def send_to_dbr(self, mtype, channelName, sid, access_data):
        cStatus = None
        v_result = self.verify_acccess_response(access_data)
        if not v_result["result"]:
            await self.failure_dispatcher(mtype, sid, v_result["msg"])
            return
        access_token = v_result["token"]
        if mtype == 0:
            cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.SUBSCRIBE_TO_CHANNEL,
                                              channelName, sid, access_token)
        else:
            cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.CONNECT_TO_CHANNEL,
                                              channelName, sid, access_token)
        if not cStatus:
            await self._failure_dispatcher(mtype, sid, "library is not connected with the dbridges network")


    async def communicate(self, mtype, channelName, mprivate, action):
        cStatus = False
        m_channel = None
        m_value = None
        access_token = None
        sid = util.GenerateUniqueId()
        if not mprivate:
            if mtype == 0:
                cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.SUBSCRIBE_TO_CHANNEL,
                                                        channelName, sid, access_token)
            else:
                cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.CONNECT_TO_CHANNEL,
                                                        channelName, sid, access_token)
            if not cStatus:
                if mtype == 0:
                    raise dBError.dBError("E024")
                else:
                    raise dBError.dBError("E090")
        else:
            response = accessResponse.privateResponse(1, mtype, channelName, sid, self)
            await self.__dbcore.accesstoken_dispatcher(channelName, action, response)

        if mtype == 0:
            m_channel = subscribeChannel.channel(channelName, sid, self.__dbcore)
            m_value = {"name": channelName, "type": "s", "status": channelState.states.SUBSCRIPTION_INITIATED,
                       "ino": m_channel}
        else:
            m_channel = connectChannel.channelnbd(channelName, sid, self.__dbcore)
            m_value = {"name": channelName, "type": "c", "status": channelState.states.CONNECTION_INITIATED,
                       "ino": m_channel}

        self.__channelsid_registry[sid] = m_value
        self.__channelname_sid[channelName] = sid
        return m_channel

    async def subscribe(self, channelName):
        access_token = None
        if str(channelName).lower() != "sys:*":
            try:
                self.validateChanelName(channelName)
            except dBError.dBError as dberror:
                raise dberror

        if channelName in self.__channelname_sid:
            raise dBError.dBError("E093")


        m_channel = None
        m_actiontype = None
        mprivate = self.isPrivateChannel(channelName)

        if str(channelName).lower().startswith("sys:"):
            m_actiontype = dBToken.tokenTypes.SYSTEM_CHANNELSUBSCRIBE.value
        else:
            m_actiontype = dBToken.tokenTypes.CHANNELSUBSCRIBE.value


        try:
            m_channel = await self.communicate(0, channelName, mprivate, m_actiontype)
        except dBError.dBError as dberror:
            raise dberror
        return m_channel

    async def connect(self, channelName):
        access_token = None
        if str(channelName).lower() != "sys:*":
            try:
                self.validateChanelName(channelName , 1)
            except dBError.dBError as dberror:
                raise dberror


        mprivate = None
        m_channel = None
        m_actiontype = None
        if str(channelName).lower().startswith("sys:"):
            raise dBError.dBError("E095")

        if channelName in self.__channelname_sid:
            raise dBError.dBError("E094")

        mprivate = self.isPrivateChannel(channelName)
        m_channel = None

        try:
            m_channel = await self.communicate(1, channelName, mprivate, dBToken.tokenTypes.CHANNELCONNECT.value)
        except dBError.dBError as dberror:
            raise dberror
        return m_channel

    async def unsubscribe(self, channelName):
        if channelName not in self.__channelname_sid:
            raise dBError.dBError("E030")

        sid = self.__channelname_sid[channelName]
        m_object = self.__channelsid_registry[sid]
        m_status = False
        if m_object["type"] != "s":
            raise dBError.dBError("E096")

        if m_object["status"] == channelState.states.UNSUBSCRIBE_INITIATED:
            raise dBError.dBError("E097")

        if m_object["status"] == channelState.states.SUBSCRIPTION_ACCEPTED or \
                m_object["status"] == channelState.states.SUBSCRIPTION_INITIATED or \
                m_object["status"] == channelState.states.SUBSCRIPTION_PENDING or \
                m_object["status"] == channelState.states.SUBSCRIPTION_ERROR or \
                m_object["status"] == channelState.states.UNSUBSCRIBE_ERROR:
            m_status = await util.updatedBNewtworkSC(self.__dbcore,
                                               dBTypes.messageType.UNSUBSCRIBE_DISCONNECT_FROM_CHANNEL,
                                               channelName, sid, None)

        if not m_status:
            raise dBError.dBError("E098")
        self.__channelsid_registry[sid]["status"] = channelState.states.UNSUBSCRIBE_INITIATED


    async def disconnect(self, channelName):
        if channelName not in self.__channelname_sid:
            raise dBError.dBError("E099")

        sid = self.__channelname_sid[channelName]
        m_object = self.__channelsid_registry[sid]
        m_status = False
        if m_object["type"] != "c":
            raise dBError.dBError("E100")

        if m_object["status"] == channelState.states.DISCONNECT_INITIATED:
            raise dBError.dBError("E101")

        if m_object["status"] == channelState.states.CONNECTION_ACCEPTED or \
                m_object["status"] == channelState.states.CONNECTION_INITIATED or \
                m_object["status"] == channelState.states.CONNECTION_PENDING or \
                m_object["status"] == channelState.states.CONNECTION_ERROR or \
                m_object["status"] == channelState.states.DISCONNECT_ERROR:
            m_status = await util.updatedBNewtworkSC(self.__dbcore,
                                               dBTypes.messageType.UNSUBSCRIBE_DISCONNECT_FROM_CHANNEL,
                                               channelName, sid, None)

        if not m_status:
            raise dBError.dBError("E102")
        self.__channelsid_registry[sid]["status"] = channelState.states.DISCONNECT_INITIATED



    async def handleSubscribeEvents(self, eventNames, eventData, m_object):
        for eventName in eventNames:
            tmatadata = self.__metadata.copy()
            tmatadata["channelname"] = m_object["ino"].getChannelName()
            tmatadata["eventname"] = eventName.value

            await self.__dispatch.emit_channel(eventName, eventData, tmatadata)
            await m_object["ino"].emit_channel(eventName, eventData, tmatadata)


    async def updateSubscribeStatus(self, sid, status, reason):
        if sid not in self.__channelsid_registry:
            return
        m_object = self.__channelsid_registry[sid]
        if m_object["type"] == "s":
            if status == channelState.states.SUBSCRIPTION_ACCEPTED:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self.handleSubscribeEvents([dBEvents.systemEvents.SUBSCRIBE_SUCCESS, dBEvents.systemEvents.ONLINE], "",
                                           m_object)
            else:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self.handleSubscribeEvents([dBEvents.systemEvents.SUBSCRIBE_FAIL], reason, m_object)
                del self.__channelname_sid[m_object["name"]]
                del self.channelsid_registry[sid]
        if m_object["type"] == "c":
            if status == channelState.states.CONNECTION_ACCEPTED:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self.handleSubscribeEvents([dBEvents.systemEvents.CONNECT_SUCCESS, dBEvents.systemEvents.ONLINE], "", m_object)
            else:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self.handleSubscribeEvents([dBEvents.systemEvents.CONNECT_FAIL], reason, m_object)
                del self.__channelname_sid[m_object["name"]]
                del self.__channelsid_registry[sid]

    async def updateSubscribeStatusRepeat(self, sid, status, reason):
        if sid not in self.__channelsid_registry:
            return
        m_object = self.__channelsid_registry[sid]
        if m_object["type"] == "s":
            if status == channelState.states.SUBSCRIPTION_ACCEPTED:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self.handleSubscribeEvents(  [dBEvents.systemEvents.RESUBSCRIBE_SUCCESS, dBEvents.systemEvents.ONLINE], "", m_object)
            else:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self.handleSubscribeEvents([dBEvents.systemEvents.OFFLINE], reason, m_object)
                del self.__channelname_sid[m_object["name"]]
                del self.channelsid_registry[sid]
        if m_object["type"] == "c":
            if status == channelState.states.CONNECTION_ACCEPTED:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self.handleSubscribeEvents([dBEvents.systemEvents.RECONNECT_SUCCESS, dBEvents.systemEvents.ONLINE], "", m_object)
            else:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self.handleSubscribeEvents([dBEvents.systemEvents.OFFLINE], reason, m_object)
                del self.__channelname_sid[m_object["name"]]
                del self.channelsid_registry[sid]

    async def updateChannelsStatusAddChange(self, life_cycle, sid, status, reason):
        if life_cycle == 0:
            await self.updateSubscribeStatus(sid, status, reason)
        else:
            await self.updateSubscribeStatusRepeat(sid, status, reason)

    async def updateChannelsStatusRemove(self, sid, status, reason):
        if sid not in self.__channelsid_registry:
            return
        m_object = self.__channelsid_registry[sid]
        if m_object["type"] == "s":
            if status == channelState.states.UNSUBSCRIBE_ACCEPTED:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self.handleSubscribeEvents([dBEvents.systemEvents.UNSUBSCRIBE_SUCCESS, dBEvents.systemEvents.REMOVE], reason,
                                           m_object)
                del self.__channelname_sid[m_object["name"]]
                del self.__channelsid_registry[sid]
            else:
                self.__channelsid_registry[sid]["status"] = channelState.states.SUBSCRIPTION_ACCEPTED
                m_object["ino"].set_isOnline(True)
                await self.handleSubscribeEvents([dBEvents.systemEvents.UNSUBSCRIBE_FAIL, dBEvents.systemEvents.ONLINE], reason,
                                           m_object)

        if m_object["type"] == "c":
            if status == channelState.states.DISCONNECT_ACCEPTED:
                self.__channelsid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self.handleSubscribeEvents([dBEvents.systemEvents.DISCONNECT_SUCCESS, dBEvents.systemEvents.REMOVE],
                                           reason, m_object)
                del self.__channelname_sid[m_object["name"]]
                del self.__channelsid_registry[sid]
            else:
                self.__channelsid_registry[sid]["status"] = channelState.states.DISCONNECT_ACCEPTED
                m_object["ino"].set_isOnline(True)
                await self.handleSubscribeEvents([dBEvents.systemEvents.DISCONNECT_FAIL, dBEvents.systemEvents.ONLINE], reason,
                                           m_object)

    def _isonline(self, sid):
        if sid not in self.__channelsid_registry:
            return False
        m_object = self.__channelsid_registry[sid]
        if m_object["status"] == channelState.states.CONNECTION_ACCEPTED or m_object[
            "status"] == channelState.states.SUBSCRIPTION_ACCEPTED:
            return True
        return False

    def isOnline(self, channelName):
        if channelName not in self.__channelname_sid:
            raise Exception("channel name does not exists")
        if not self.__dbcore.isSocketConnected():
            return False

        sid = self.__channelname_sid[channelName]
        return self._isonline(sid)

    def list(self):
        m_data = []
        for (k, v) in self.__channelsid_registry.items():
            i_data = {}
            i_data["name"] = v["name"]
            if v["type"] == "s":
                i_data["type"] = "subscribed"
            else:
                i_data["type"] = "connect"
            i_data["isonline"] = self._isonline(k)
            m_data.append(i_data)
        return m_data

    async def send_OfflineEvents(self):
        for (k, v) in self.__channelsid_registry.items():
            await self.handleSubscribeEvents([dBEvents.systemEvents.OFFLINE], "", v)

    def get_subscribeStatus(self, sid):
        return self.__channelsid_registry[sid]["status"]

    def get_channelType(self, sid):
        if sid not in self.__channelsid_registry:
            return ""
        return self.__channelsid_registry[sid]["type"]

    def get_channelName(self, sid):
        if sid not in self.__channelsid_registry:
            return None
        return self.__channelsid_registry[sid]["name"]

    def getConnectStatus(self, sid):
        return self.__channelsid_registry[sid]["status"]

    def getChannel(self, sid):
        if sid not in self.__channelsid_registry:
            return None
        return self.__channelsid_registry[sid]["ino"]

    def getChannelName(self, sid):
        if sid not in self.__channelsid_registry:
            return None
        return self.__channelsid_registry[sid]["name"]

    def isSubscribedChannel(self, sid):
        if sid not in self.__channelsid_registry:
            return False
        if self.__channelsid_registry[sid]["type"] == "s":
            return self.__channelsid_registry[sid]["ino"].isSubscribed
        else:
            return False

    def __clean_channel(self, sid):
        if sid not in self.__channelsid_registry:
            return

        m_object = self.__channelsid_registry[sid]
        m_object["ino"].set_isOnline(False)
        if m_object["type"] == "s":
            m_object["ino"].unbind(None, None)
            m_object["ino"].unbind_all(None)
        else:
            m_object["ino"].unbind(None, None)

    async def cleanUp_All(self):
        temp_coppied = self.__channelname_sid.copy()
        for (k, v) in temp_coppied.items():
            metadata = self.__metadata
            metadata["channelname"] = k
            metadata["eventname"] = "dbridges:channel.removed"


            await self.handledispatcherEvents(dBEvents.systemEvents.REMOVE, "", k, metadata)
            self.__clean_channel(v)
            del self.__channelname_sid[k]
            del self.__channelsid_registry[v]
        #self.__dispatch.unbind(None, None)
        #self.__dispatch.unbind_all(None)

