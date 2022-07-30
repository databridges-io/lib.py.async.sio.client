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

import asyncio
import math
import random

async def updatedBNewtworkSC(dbcore, dbmsgtype, channelName, sid, channelToken, subject=None, source_id=None, t1=None,  seqnum=None):
    if channelToken is not None:
        mpayload = channelToken.encode()
    else:
        mpayload = "".encode()

    msgDbp = {"eventname": "db",
              "dbmsgtype": dbmsgtype.value,
              "subject": subject,
              "rsub": None,
              "sid": sid,
              "payload": mpayload,
              "fenceid": channelName,
              "rspend": None,
              "rtrack": None,
              "rtrackstat": None,
              "t1": t1,
              "latency": None,
              "globmatch": 0,
              "sourceid": source_id,
              "sourceip": None,
              "replylatency": None,
              "oqueumonitorid": seqnum}

    asyncStates = await dbcore.send(msgDbp)
    return asyncStates


async def updatedBNewtworkCF(dbcore , dbmsgtype , sessionid, functionName , returnSubject , sid , payload , rspend , rtrack ):
    if payload is not None:
        mpayload = payload.encode()
    else:
        mpayload = "".encode()

    msgDbp = {"eventname": "db",
              "dbmsgtype": dbmsgtype.value,
              "subject": functionName,
              "rsub": returnSubject,
              "sid": sid,
              "payload": mpayload,
              "fenceid": sessionid,
              "rspend": rspend,
              "rtrack": rtrack,
              "rtrackstat": None,
              "t1": None,
              "latency": None,
              "globmatch": 0,
              "sourceid": None,
              "sourceip": None,
              "replylatency": None,
              "oqueumonitorid": None}

    asyncStates = await dbcore.send(msgDbp)
    return asyncStates


def GenerateUniqueId():
    return ("" + str(random.randint(0, 999999)))
