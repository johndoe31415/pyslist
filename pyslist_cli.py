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

def genparser(parser):
	parser.add_argument("-d", "--dbfile", metavar = "filename", type = str, default = "pyslist.sqlite3", help = "Specifies the database file that is used. Defaults to %(default)s.")
	parser.add_argument("--verbose", action = "store_true", help = "Increase verbosity.")
	parser.add_argument("storename", metavar = "storename", type = str, help = "Name of the store the list is for.")
	parser.add_argument("itemlist", metavar = "itemlist", type = str, help = "List of items in the order they are to be appear in the database.")
mc.register("import", "Import an item list for a specific store", genparser, action = action_import_store)

def genparser(parser):
	parser.add_argument("-d", "--dbfile", metavar = "filename", type = str, default = "pyslist.sqlite3", help = "Specifies the database file that is used. Defaults to %(default)s.")
mc.register("dump", "Dump the database structure", genparser, action = action_dump)

mc.run(sys.argv[1:])
