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

class privateResponse:

    def __init__(self, m_class_type, m_type, name, sid, rcCore):
        self.__name = name
        self.__rcCore = rcCore
        self.__mtype = m_type
        self.__m_class_type = m_class_type
        self.__sid = sid

    async def end(self, data):
        if self.__m_class_type ==  1:
            await self.__rcCore.send_to_dbr(self.__mtype, self.__name, self.__sid, data)
        else:
            await self.__rcCore.send_to_dbr(self.__name, self.__sid, data)

    async def exception(self, info):
        vresult = {"statuscode": 9, "error_message": info, "accesskey": None}
        if self.__m_class_type == 1:
            await self.__rcCore.send_to_dbr(self.__mtype, self.__name, self.__sid, vresult)
        else:
            await self.__rcCore.send_to_dbr(self.__name, self.__sid, vresult)
