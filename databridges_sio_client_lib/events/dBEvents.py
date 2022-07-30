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
from enum import Enum


class systemEvents(Enum):
    SUBSCRIBE_SUCCESS = "dbridges:subscribe.success"
    SUBSCRIBE_FAIL = "dbridges:subscribe.fail"
    ONLINE = "dbridges:channel.online"
    OFFLINE = "dbridges:channel.offline"
    REMOVE = "dbridges:channel.removed"
    UNSUBSCRIBE_SUCCESS = "dbridges:unsubscribe.success"
    UNSUBSCRIBE_FAIL = "dbridges:unsubscribe.fail"
    CONNECT_SUCCESS = "dbridges:connect.success"
    CONNECT_FAIL = "dbridges:connect.fail"
    DISCONNECT_SUCCESS = "dbridges:disconnect.success"
    DISCONNECT_FAIL = "dbridges:disconnect.fail"
    RESUBSCRIBE_SUCCESS = "dbridges:resubscribe.success"
    RESUBSCRIBE_FAIL = "dbridges:resubscribe.fail"
    RECONNECT_SUCCESS = "dbridges:reconnect.success"
    RECONNECT_FAIL = "dbridges:reconnect.fail"
    PARTICIPANT_JOINED = "dbridges:participant.joined"
    PARTICIPANT_LEFT = "dbridges:participant.left"

    REGISTRATION_SUCCESS = "dbridges:rpc.server.registration.success"
    REGISTRATION_FAIL = "dbridges:rpc.server.registration.fail"
    SERVER_ONLINE = "dbridges:rpc.server.online"
    SERVER_OFFLINE = "dbridges:rpc.server.offline"
    UNREGISTRATION_SUCCESS = "dbridges:rpc.server.unregistration.success"
    UNREGISTRATION_FAIL = "dbridges:rpc.server.unregistration.fail"
    RPC_CONNECT_SUCCESS = "dbridges:rpc.server.connect.success"
    RPC_CONNECT_FAIL = "dbridges:rpc.server.connect.fail"

    #RPC_RECONNECT_SUCCESS = "dbridges:server.reconnect.success"
    #RPC_RECONNECT_FAIL = "dbridges:server.reconnect.fail"




