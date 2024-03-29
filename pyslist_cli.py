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

import sys
import json
import requests
import uuid
from MultiCommand import MultiCommand
from ShoppingListDB import ShoppingListDB

mc = MultiCommand()
def action_import_store(cmd, args):
	next_id = 0
	item_ordernos = { }
	with open(args.itemlist) as f:
		for (lineno, line) in enumerate(f, 1):
			line = line.strip("\r\n\t ")
			if line == "":
				continue
			if line.startswith("="):
				next_id = -1
			else:
				item_name = line

				if next_id != -1:
					next_id = next_id + 1
				if item_name in item_ordernos:
					print("Warning: Item '%s' more than once in item list at line %d." % (item_name, lineno))
				item_ordernos[item_name] = next_id

	db = ShoppingListDB(args.dbfile)
	storeid = db.add_store(args.storename)
	db.reset_store_order(storeid)
	itemids = db.add_items(item_ordernos.keys())

	ordernos = { itemids[itemname]: item_ordernos[itemname] for itemname in item_ordernos }
	db.set_store_order(storeid, ordernos)

def action_dump(cmd, args):
	db = ShoppingListDB(args.dbfile)
	print(json.dumps(db.get_all(), indent = 4, sort_keys = True))

def action_remote(cmd, args):
	session = requests.Session()
	post_data = None
	if args.call == "debug":
		method = session.get
		uri = args.base_uri + "/debug"
	elif args.call == "all":
		method = session.get
		uri = args.base_uri + "/all"
	elif args.call == "transaction":
		method = session.post
		uri = args.base_uri + "/transaction"
		post_data = {
			"transactionid":	str(uuid.uuid4()),
			"itemid":	10,
			"delta":	1,
		}
	else:
		raise NotImplementedError(args.call)

	if post_data is not None:
		post_data = json.dumps(post_data).encode()

	response = method(uri, auth = requests.auth.HTTPDigestAuth(args.username, args.password), data = post_data)
	if response.status_code != 200:
		print(response)
		print("=" * 120)
		print(response.text)
	else:
		print(json.dumps(response.json(), indent = 4, sort_keys = True))

def genparser(parser):
	parser.add_argument("-d", "--dbfile", metavar = "filename", type = str, default = "pyslist.sqlite3", help = "Specifies the database file that is used. Defaults to %(default)s.")
	parser.add_argument("--verbose", action = "store_true", help = "Increase verbosity.")
	parser.add_argument("storename", metavar = "storename", type = str, help = "Name of the store the list is for.")
	parser.add_argument("itemlist", metavar = "itemlist", type = str, help = "List of items in the order they are to be appear in the database.")
mc.register("import", "Import an item list for a specific store", genparser, action = action_import_store)

def genparser(parser):
	parser.add_argument("-d", "--dbfile", metavar = "filename", type = str, default = "pyslist.sqlite3", help = "Specifies the database file that is used. Defaults to %(default)s.")
mc.register("dump", "Dump the database structure", genparser, action = action_dump)

def genparser(parser):
	parser.add_argument("-c", "--call", choices = [ "debug", "all", "transaction" ], default = "debug", help = "Call to execute on the remote side. Can be one of %(choices)s, defaults to %(default)s.")
	parser.add_argument("-u", "--username", metavar = "username", default = "joe", help = "Username to authenticate against on the remote side. Defaults to %(default)s.")
	parser.add_argument("-p", "--password", metavar = "password", default = "foobar", help = "Password to authenticate with on the remote side. Defaults to %(default)s.")
	parser.add_argument("base_uri", metavar = "uri", type = str, help = "API endpoint URI on the remote side.")
mc.register("remote", "Access API calls on the remote", genparser, action = action_remote)

mc.run(sys.argv[1:])
