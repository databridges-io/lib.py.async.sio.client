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
    SUBSCRIPTION_INITIATED = "subscription_initiated"
    SUBSCRIPTION_PENDING = "subscription_pending"
    SUBSCRIPTION_ACCEPTED = "subscription_accepted"
    SUBSCRIPTION_ERROR = "subscription_error"

    CONNECTION_INITIATED = "connection_initiated"
    CONNECTION_PENDING = "connection_pending"
    CONNECTION_ACCEPTED = "connection_accepted"
    CONNECTION_ERROR = "connection_error"

    UNSUBSCRIBE_INITIATED = "unsubscribe_initiated"
    UNSUBSCRIBE_ACCEPTED = "unsubscribe_accepted"
    UNSUBSCRIBE_ERROR = "unsubscribe_error"

    DISCONNECT_INITIATED = "disconnect_initiated"
    DISCONNECT_ACCEPTED = "disconnect_accepted"
    DISCONNECT_ERROR = "disconnect_error"
