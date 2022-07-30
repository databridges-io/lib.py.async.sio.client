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


class messageType(Enum):
    SUBSCRIBE_TO_CHANNEL = 11
    CONNECT_TO_CHANNEL = 12
    UNSUBSCRIBE_DISCONNECT_FROM_CHANNEL = 13
    PUBLISH_TO_CHANNEL = 16

    SERVER_SUBSCRIBE_TO_CHANNEL= 111

    SERVER_UNSUBSCRIBE_DISCONNECT_FROM_CHANNEL= 113
    SERVER_PUBLISH_TO_CHANNEL= 116
    SERVER_CHANNEL_SENDMSG= 117
    LATENCY = 99
    SYSTEM_MSG = 0
    PARTICIPANT_JOIN = 17
    PARTICIPANT_LEFT = 18
    CF_CALL_RECEIVED = 44
    CF_CALL = CF_CALL_RECEIVED
    CF_CALL_RESPONSE = 46
    CF_RESPONSE_TRACKER = 48
    CF_CALLEE_QUEUE_EXCEEDED = 50

    REGISTER_RPC_SERVER = 51
    UNREGISTER_RPC_SERVER = 52
    CONNECT_TO_RPC_SERVER = 53
    CALL_RPC_FUNCTION = 54
    RPC_CALL_RECEIVED = CALL_RPC_FUNCTION
    CALL_CHANNEL_RPC_FUNCTION = 55
    RPC_CALL_RESPONSE = 56
    RPC_CALL_TIMEOUT = 59
    RPC_RESPONSE_TRACKER = 58
    RPC_CALLEE_QUEUE_EXCEEDED = 60