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

from ..events import dBEvents

channelConnectEvent = [dBEvents.systemEvents.CONNECT_SUCCESS.value,
                          dBEvents.systemEvents.CONNECT_FAIL.value,
                          dBEvents.systemEvents.RECONNECT_SUCCESS.value,
                          dBEvents.systemEvents.RECONNECT_FAIL.value,
                          dBEvents.systemEvents.DISCONNECT_SUCCESS.value,
                          dBEvents.systemEvents.DISCONNECT_FAIL.value,
                          dBEvents.systemEvents.ONLINE.value,
                          dBEvents.systemEvents.OFFLINE.value,
                          dBEvents.systemEvents.REMOVE.value,
                          dBEvents.systemEvents.PARTICIPANT_JOINED.value,
                          dBEvents.systemEvents.PARTICIPANT_LEFT.value]
