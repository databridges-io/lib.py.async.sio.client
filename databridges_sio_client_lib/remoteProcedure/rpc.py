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
from datetime import datetime
import re
import time
from ..Tokens import dBToken
from ..messageTypes import dBTypes
from ..commonUtils import util
from ..dispatchers import dispatcher
from ..exceptions import dBError
from ..remoteProcedure import rpcState
from ..responseHandler import cfrpcResponse
from ..remoteProcedure import rpcClient
from ..privateAccess import accessResponse
from ..events import dBEvents

class CRpc():
    def __init__(self, dBCoreObject):
        self.__server_type = ["pvt", "prs", "sys"]
        self.__serverSid_registry = dict()
        self.__serverName_sid = dict()
        self.__dbcore = dBCoreObject
        self.__dispatch = dispatcher.dispatcher()
        self.__metadata = {"servername": None, "eventname": None, "sourcesysid": None,
                           "sqnum": None, "sessionid": None, "intime": None}
        self.__callersid_object = dict()

    def isEmptyOrSpaces(self, str):
        if str and str.strip():
            return False
        else:
            return True

    def validateServerName(self, serverName, error_type=0):
        if not self.__dbcore.connectionstate.isconnected:
            if error_type == 1:
                raise dBError.dBError("E053")
        if type(serverName) is not str:
            if error_type == 1:
                raise dBError.dBError("E048")

        if self.isEmptyOrSpaces(serverName):
            if error_type == 1:
                raise dBError.dBError("E051")

        if len(serverName) > 64:
            if error_type == 1:
                raise dBError.dBError("E051")

        if not re.match('^[a-zA-Z0-9\.:_-]*$', serverName):
            if error_type == 1:
                raise dBError.dBError("E052")

        if ":" in serverName:
            sdata = serverName.lower().split(":")
            if sdata[0] not in self.__server_type:
                if error_type == 1:
                    raise dBError.dBError("E052")

    def issidExists(self, sid):
        if sid in self.__serverSid_registry.keys():
            return True
        else:
            return False

    def get_rpcStatus(self, sid):
        return self.__serverSid_registry[sid]["status"]

    def bind(self, eventName, callback):
        self.__dispatch.bind(eventName, callback)

    def unbind(self, eventName, callback=None):
        self.__dispatch.unbind(eventName, callback)

    def bind_all(self, callback):
        self.__dispatch.bind_all(callback)

    def unbind_all(self, callback=None):
        self.__dispatch.unbind_all(callback)

    def isPrivateServer(self, serverName):
        flag = False
        if ":" in serverName:
            sdata = serverName.lower().split(":")
            if sdata[0] in self.__server_type:
                flag = True
        return flag

    async def communicateR(self, mtype, serverName, sid, access_token):
        cStatus = False
        if mtype == 0:
            cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.REGISTER_RPC_SERVER, serverName, sid,
                                              access_token)
        else:
            cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.CONNECT_TO_RPC_SERVER, serverName, sid,
                                              access_token)

        if not cStatus:
            if mtype == 0:
                raise dBError.dBError("E057")
            else:
                raise dBError.dBError("E053")

    async def _ReSubscribe(self, sid):
        m_object = self.__serverSid_registry[sid]
        access_token = None
        mprivate =  self.isPrivateServer(m_object["name"])


        if m_object["status"] == rpcState.states.RPC_CONNECTION_ACCEPTED or m_object[
            "status"] == rpcState.states.RPC_CONNECTION_INITIATED:
            try:
                access_token=  dBToken.tokenTypes.RPCCONNECT.value
                if not mprivate:
                    await self.communicateR(1, m_object["name"], sid, access_token)
                else:
                    response = accessResponse.privateResponse(2, 1, m_object["name"], sid, self)
                    await self.__dbcore.accesstoken_dispatcher(m_object["name"], access_token, response)

            except dBError.dBError as error:
                await self._handleRegisterEvents\
                    ([dBEvents.systemEvents.RPC_CONNECT_FAIL], error, m_object)
                return

    async def ReSubscribeAll(self):
        for (k, v) in self.__serverName_sid.items():
            for (k2, v2) in v.items():
                await self._ReSubscribe(k2)


    async def handledispatcherEvents(self, eventName, eventInfo=None, serverName=None, metadata=None):
        try:
            if serverName:
                await self.__dispatch.emit(eventName, eventInfo, metadata)
                sid = self.__serverName_sid[serverName]
                m_object = self.__serverSid_registry[sid]
                if m_object:
                    await m_object["ino"].emit(eventName, eventInfo, serverName, metadata)
        except Exception as e:
            pass

    def get_rpcStatus(self, sid):
        return self.__serverSid_registry[sid]["status"]

    async def _handleRegisterEvents(self, eventNames, eventData, m_object):
        for eventName in eventNames:
            tmatadata = self.__metadata.copy()
            
            tmatadata["servername"] = m_object["ino"].getServerName()
            tmatadata["eventname"] = eventName.value
            tmatadata["sessionid"] =  self.__dbcore.sessionid
            tmatadata["intime"] =   round(time.time())
            await self.__dispatch.emit_channel(eventName, eventData, tmatadata)
            await m_object["ino"].emit_channel(eventName, eventData, tmatadata)


    async def _updateRegistrationStatus(self, sid, status, reason):
        if sid not in self.__serverSid_registry:
            return
        m_object = self.__serverSid_registry[sid]
        if m_object["type"] == "r":
            if status == rpcState.states.REGISTRATION_ACCEPTED:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self._handleRegisterEvents([dBEvents.systemEvents.REGISTRATION_SUCCESS, dBEvents.systemEvents.SERVER_ONLINE],
                                           "", m_object)
            else:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self._handleRegisterEvents([dBEvents.systemEvents.REGISTRATION_FAIL], reason, m_object)
                #del self.__serverName_sid[m_object["name"]]
                if sid in self.__serverName_sid[m_object["name"]].keys():
                    del self.__serverName_sid[m_object["name"]][sid]
                    if len(self.__serverName_sid[m_object["name"]].keys()) == 0:
                        del self.__serverName_sid[m_object["name"]]
                del self.__serverSid_registry[sid]
        if m_object["type"] == "c":
            if status == rpcState.states.RPC_CONNECTION_ACCEPTED:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self._handleRegisterEvents([dBEvents.systemEvents.RPC_CONNECT_SUCCESS, dBEvents.systemEvents.SERVER_ONLINE], "",
                                           m_object)
            else:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self._handleRegisterEvents([dBEvents.systemEvents.RPC_CONNECT_FAIL], reason, m_object)
                #del self.__serverName_sid[m_object["name"]]
                if sid in self.__serverName_sid[m_object["name"]].keys():
                    del self.__serverName_sid[m_object["name"]][sid]
                    if len(self.__serverName_sid[m_object["name"]].keys()) == 0:
                        del self.__serverName_sid[m_object["name"]]
                del self.__serverSid_registry[sid]

    async def _updateRegistrationStatusRepeat(self, sid, status, reason):
        if sid not in self.__serverSid_registry:
            return
        m_object = self.__serverSid_registry[sid]
        if m_object["type"] == "r":
            if status == rpcState.states.REGISTRATION_ACCEPTED:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self._handleRegisterEvents([dBEvents.systemEvents.SERVER_ONLINE], "",
                                           m_object)
            else:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self._handleRegisterEvents([dBEvents.systemEvents.SERVER_OFFLINE], reason, m_object)
                if sid in self.__serverName_sid[m_object["name"]].keys():
                    del self.__serverName_sid[m_object["name"]][sid]
                    if len(self.__serverName_sid[m_object["name"]].keys()) == 0:
                        del self.__serverName_sid[m_object["name"]]

                del self.__serverSid_registry[sid]
        if m_object["type"] == "c":
            if status == rpcState.states.RPC_CONNECTION_ACCEPTED:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(True)
                await self._handleRegisterEvents([dBEvents.systemEvents.SERVER_ONLINE], "", m_object)
            else:
                self.__serverSid_registry[sid]["status"] = status
                m_object["ino"].set_isOnline(False)
                await self._handleRegisterEvents([dBEvents.systemEvents.SERVER_OFFLINE], reason, m_object)
                if sid in self.__serverName_sid[m_object["name"]].keys():
                    del self.__serverName_sid[m_object["name"]][sid]
                    if len(self.__serverName_sid[m_object["name"]].keys()) == 0:
                        del self.__serverName_sid[m_object["name"]]
                del self.__serverSid_registry[sid]

    async def updateRegistrationStatusAddChange(self, life_cycle, sid, status, reason):
        if life_cycle == 0:
            await self._updateRegistrationStatus(sid, status, reason)
        else:
            await self._updateRegistrationStatusRepeat(sid, status, reason)

    async def communicate(self, serverName, mprivate, action):
        cStatus = False

        m_value = None
        access_token = None
        sid = util.GenerateUniqueId()
        if not mprivate:
            cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.CONNECT_TO_RPC_SERVER,
                                              serverName, sid, access_token)
            if not cStatus:
                raise dBError.dBError("E053")
        else:
            response = accessResponse.privateResponse(2 , 1,   serverName, sid, self)
            await self.__dbcore.accesstoken_dispatcher(serverName, action, response)

        rpccaller = rpcClient.CrpCaller(serverName, self.__dbcore, self)
        m_value = {"name": serverName, "type": "c",
                   "status": rpcState.states.RPC_CONNECTION_INITIATED, "ino": rpccaller}

        self.__serverSid_registry[sid] = m_value

        if serverName not in self.__serverName_sid.keys():
            self.__serverName_sid[serverName] = dict()
            self.__serverName_sid[serverName][sid] = ""
        else:
            self.__serverName_sid[serverName][sid] = ""

        return rpccaller

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

    async def failure_dispatcher(self, sid, reason):
        m_object = self.__serverSid_registry[sid]
        m_object["ino"].set_isOnline(False)

        dberror = dBError.dBError("E104")
        dberror.updatecode("", reason)
        await self._handleRegisterEvents([dBEvents.systemEvents.RPC_CONNECT_FAIL], dberror, m_object)
        #del self.__serverName_sid[m_object["name"]]
        if sid in self.__serverName_sid[m_object["name"]].keys():
            del self.__serverName_sid[m_object["name"]][sid]
            if len(self.__serverName_sid[m_object["name"]].keys()) == 0:
                del self.__serverName_sid[m_object["name"]]

        del self.__serverSid_registry[sid]

    async def send_to_dbr(self, channelName, sid, access_data):
        cStatus = None
        v_result = self.verify_acccess_response(access_data)
        if not v_result["result"]:
            await self.failure_dispatcher(sid, v_result["msg"])
            return

        access_token = v_result["token"]
        cStatus = await util.updatedBNewtworkSC(self.__dbcore, dBTypes.messageType.CONNECT_TO_RPC_SERVER,
                                          channelName, sid, access_token)
        if not cStatus:
            await self._failure_dispatcher(sid, "library is not connected with the dbridges network")

    async def connect(self, serverName):
        access_token = None
        try:
            self.validateServerName(serverName, 1)
        except dBError.dBError as dberror:
            raise dberror


        mprivate = self.isPrivateServer(serverName)
        m_caller = None
        m_actiontype = None
        m_actiontype = dBToken.tokenTypes.RPCCONNECT.value

        try:
            m_caller = await self.communicate(serverName, mprivate, m_actiontype)
        except dBError as dberror:
            raise dberror
        return m_caller



    def ChannelCall(self, serverName):
        if serverName in self.__serverName_sid.keys():
            #sid = self.__serverName_sid[serverName]
            sids = self.__serverName_sid[serverName]
            sid = sids.keys()[0]
            mobject = self.__serverSid_registry[sid]
            self.__serverSid_registry[sid]["count"] = mobject["count"] + 1
            return mobject
        else:
            sid = util.GenerateUniqueId()
            rpccaller = rpcClient.CrpCaller(serverName, self.__dbcore, self, "ch")
            #self.__serverName_sid[serverName] = sid

            if serverName not in self.__serverName_sid.keys():
                self.__serverName_sid[serverName] = {}
                self.__serverName_sid[serverName][sid] = ""
            else:
                self.__serverName_sid[serverName][sid] = ""



            m_value = {"name": serverName, "type": "x", "status": rpcState.states.RPC_CONNECTION_INITIATED,
                       "ino": rpccaller,
                       "count": 1}
            self.__serverSid_registry[sid] = m_value
            return rpccaller



    def store_object(self, sid, rpccaller):
        self.__callersid_object[sid] = rpccaller

    def delete_object(self, sid):
        del self.__callersid_object[sid]

    def get_object(self, sid):
        if sid in self.__callersid_object.keys():
            return self.__callersid_object[sid]
        else:
            return None

    def get_rpcServerObject(self, sid):
        if sid in self.__serverSid_registry.keys():
            return self.__serverSid_registry[sid]["ino"]
        else:
            return None

    async def send_OfflineEvents(self):
        for (k, v) in self.__serverSid_registry.items():
            if v["type"] == "c" or v["type"] == "r":
                await self._handleRegisterEvents([dBEvents.systemEvents.SERVER_OFFLINE], "", v)


    def clean_registry(self, sid):
        if sid not in self.__serverSid_registry:
            return False
        else:
            mobject = self.__serverSid_registry[sid]
            if mobject["type"] == "r":
                return  False
            else:
                if mobject["type"] == "c":
                    mobject["ino"].unbind(None , None)
                    return True
                else:
                    return False


    async def cleanUp_All(self):
        try:
            serverName_sid_copy = {**self.__serverName_sid}
            for (k,v) in serverName_sid_copy.items():
                for(k2, v2) in v.items():
                    excludeflag =  self.clean_registry(k2)
                    if excludeflag:
                        del self.__serverSid_registry[k2]
                del self.__serverName_sid[k]
        except Exception as e:
            pass
        
