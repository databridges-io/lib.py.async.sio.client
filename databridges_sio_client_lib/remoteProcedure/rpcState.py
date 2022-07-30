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


class states(Enum):
    REGISTRATION_INITIATED = "registration_initiated"
    REGISTRATION_PENDING = "registration_pending"
    REGISTRATION_ACCEPTED = "registration_accepted"
    REGISTRATION_ERROR = "registration_error"

    RPC_CONNECTION_INITIATED = "rpc_connection_initiated"
    RPC_CONNECTION_PENDING = "rpc_connection_pending"
    RPC_CONNECTION_ACCEPTED = "rpc_connection_accepted"
    RPC_CONNECTION_ERROR = "rpc_connection_error"

    UNREGISTRATION_INITIATED = "unregister_initiated"
    UNREGISTRATION_ACCEPTED = "unregister_accepted"
    UNREGISTRATION_ERROR = "unregister_error"

    RPC_DISCONNECT_INITIATED = "rpc_disconnect_initiated"
    RPC_DISCONNECT_ACCEPTED = "rpc_disconnect_accepted"
    RPC_DISCONNECT_ERROR = "rpc_disconnect_error"
