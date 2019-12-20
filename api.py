#!/usr/bin/python3
#	pyslist - Python-based shopping list
#	Copyright (C) 2019-2019 Johannes Bauer
#
#	This file is part of pyslist.
#
#	pyslist is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	pyslist is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with pyslist; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
from Configuration import Configuration
from ShoppingListDB import ShoppingListDB

class APIServer():
	def __init__(self):
		self._config = Configuration.default()
		self._database = ShoppingListDB(sqlite_dbfile = config.db_filename)

	def execute(self):
		response = {
			"success": True,
			"vars": os.environ,
		}
		return response

print("Content-Type: application/json")
print()

try:
	api_server = APIServer()
	response = api_server.execute()
except Exception as e:
	response = {
		"success": False,
		"error_text": "Exception: %s" % (str(e)),
	}
print(json.dumps(response))
