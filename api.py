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
import sys
import json
from Configuration import Configuration
from ShoppingListDB import ShoppingListDB

class APIServer():
	def __init__(self, config):
		self._config = config
		self._database = ShoppingListDB(sqlite_dbfile = self._config.db_filename)

	def _execute_GET_all(self, post_data, auth_user):
		return {
			"success": True,
			"msg": "all",
			"data": self._database.get_all(),
		}

	def _execute_POST_transaction(self, post_data, auth_user):
		transactionid = str(uuid.UUID(post_data.get("transactionid")))
		itemid = int(post_data.get("itemid"))
		delta = int(post_data.get("delta"))
		self._database.process_transaction(transactionid = transactionid, itemid = itemid, delta = delta, user = auth_user)
		return {
			"success": True,
			"msg": "transaction",
			"transactionid": transactionid,
		}

	def _execute_GET_debug(self, post_data, auth_user):
		return {
			"success": True,
			"msg": "debug",
			"data": {
				"env":			dict(os.environ),
				"post_data":	post_data,
				"auth_user":	auth_user,
			},
		}

	def _get_auth_user(self):
		return os.getenv("REMOTE_USER")

	def execute(self):
		request_method = os.getenv("REQUEST_METHOD")
		if request_method is not None:
			request_method = request_method.upper()
		path_info = os.getenv("PATH_INFO")
		auth_user = self._get_auth_user()

		if auth_user is None:
			return {
				"success": False,
				"error_text": "Cannot determine authenticated user.",
			}

		if request_method == "POST":
			# Decode POST data as JSON
			try:
				post_data = json.load(sys.stdin)
			except json.decoder.JSONDecodeError as e:
				return {
					"success": False,
					"error_text": "JSON decoding error: %s" % (str(e)),
				}
		else:
			post_data = None

		if (request_method == "GET") and (path_info == "/all"):
			response = self._execute_GET_all(post_data = post_data, auth_user = auth_user)
		elif (request_method == "POST") and (path_info == "/transaction"):
			response = self._execute_POST_transaction(post_data = post_data, auth_user = auth_user)
		elif (request_method == "GET") and (path_info == "/debug") and (self._config.debug):
			response = self._execute_GET_debug(post_data = post_data, auth_user = auth_user)
		else:
			response = {
				"success": False,
				"error_text": "Unknown or unsupported REQUEST_METHOD %s / PATH_INFO %s" % (str(request_method), str(path_info)),
			}
		return response

config = Configuration.default()
try:
	api_server = APIServer(config)
	response = api_server.execute()
except Exception as e:
	response = {
		"success": False,
		"error_text": "Exception: %s" % (str(e)),
	}

if (not config.debug) and ("error_text" in response):
	response["error_text"] = "Error details unavailable with disabled debugging."

print("Content-Type: application/json")
print()
print(json.dumps(response, separators = (",", ":")))
