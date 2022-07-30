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

from ..exceptions import messages, source, code


class dBError(Exception):

    def _updateClassProperty(self, ekey ,  s , c , m):
        self.__EKEY = ekey
        self.source = s
        self.code = c
        self.message = m


    def __init__(self, ekey,  codeext="" ,  message=""):
        super()
        self.source = ""
        self.code = ""
        self.message = ""
        self.__EKEY = ""
        if ekey not in messages.errorLookup.keys():
            self._updateClassProperty(ekey ,  ekey, ekey, "key is missing from the lookup tables. contact support")
            return
        value = messages.errorLookup[ekey]

        if len(value) != 2:
            self._updateClassProperty(ekey, ekey, ekey, "key , value structure is invalid. contact support")
            return
        if value[0] not in source.sourceLookup.keys():
            self._updateClassProperty(ekey, value[0], "", "source lookup key is invalid. contact support")
            return

        if value[1]not in code.codeLookup.keys():
            self._updateClassProperty(ekey, source.sourceLookup[value[0]], value[1], "code lookup key is invalid. contact support")
            return

        self._updateClassProperty(ekey, source.sourceLookup[value[0]], code.codeLookup[value[1]], "")
        if codeext:
            if self.code[-1] != '_':
                self.code = self.code + "_" + str(codeext)
            else:
                self.code = self.code + str(codeext)

        if self.isNotBlank(message):
            self.message = message



    def isBlank(self, myString):
        return not (myString and myString.strip())

    def isNotBlank(self, myString):
        return bool(myString and myString.strip())

    def updateCode(self, code, message):
        if self.isNotBlank(code):
            if self.code[-1] != '_':
                self.code = self.code + "_" + str(code)
            else:
                self.code = self.code + str(code)

        if self.isNotBlank(message):
            self.message = message

    def GetEKEY(self):
        return self.__EKEY
