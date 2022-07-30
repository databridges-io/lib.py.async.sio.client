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

connectionEvent = ["connect_error", "connected", "disconnected",
                    "reconnecting", "connecting", "state_change",
                    "reconnect_error", "reconnect_failed", "reconnected",
                    "connection_break", "rttpong"]


class states(Enum):
    CONNECTED = "connected"
    ERROR = "connect_error"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    CONNECTING = "connecting"
    STATE_CHANGE = "state_change"
    RECONNECT_ERROR = "reconnect_error"
    RECONNECT_FAILED = "reconnect_failed"
    RECONNECTED = "reconnected"
    CONNECTION_BREAK = "connection_break"

    RTTPONG = "rttpong"
    RTTPING = "rttping"
