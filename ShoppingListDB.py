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

import sqlite3
import contextlib
import datetime

class ShoppingListDB():
	def __init__(self, sqlite_dbfile):
		self._db = sqlite3.connect(sqlite_dbfile)
		self._cursor = self._db.cursor()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE items (
				itemid integer PRIMARY KEY AUTOINCREMENT,
				description varchar NOT NULL UNIQUE
			);
			""")

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE shopping_list (
				itemid integer PRIMARY KEY,
				itemcount integer NOT NULL DEFAULT 0,
				last_edited_utc timestamp NOT NULL,
				CHECK(itemcount >= 0),
				FOREIGN KEY(itemid) REFERENCES items(itemid)
			);
			""")

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE stores (
				storeid integer PRIMARY KEY AUTOINCREMENT,
				storename varchar NOT NULL UNIQUE
			);
			""")

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE storeitemorder (
				storeid integer NOT NULL,
				itemid integer NOT NULL,
				orderno integer NOT NULL,
				PRIMARY KEY(storeid, itemid),
				FOREIGN KEY(storeid) REFERENCES stores(storeid),
				FOREIGN KEY(itemid) REFERENCES items(itemid)
			);
			""")

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE history (
				transactionid uuid NOT NULL PRIMARY KEY,
				itemid integer NOT NULL,
				delta integer NOT NULL,
				user varchar NOT NULL,
				processed_utc timestamp NOT NULL,
				CHECK(delta != 0),
				FOREIGN KEY(itemid) REFERENCES items(itemid)
			);
			""")

	def get_shopping_list(self):
		return { itemid: itemcount for (itemid, itemcount) in self._cursor.execute("SELECT itemid, itemcount FROM shopping_list WHERE itemcount > 0;").fetchall() }

	def get_item_list(self):
		return { itemid: description for (itemid, description) in self._cursor.execute("SELECT itemid, description FROM items;").fetchall() }

	def _get_store_list(self):
		return { storeid: storename for (storeid, storename) in self._cursor.execute("SELECT storeid, storename FROM stores;").fetchall() }

	def _get_store_order(self, storeid):
		return { itemid: orderno for (itemid, orderno) in self._cursor.execute("SELECT storeid, itemid FROM storeitemorder WHERE storeid = ?;", (storeid, )).fetchall() }

	def get_stores(self):
		stores = { }
		for (storeid, storename) in self._get_store_list().items():
			store = {
				"storeid": storeid,
				"order": self._get_store_order(storeid),
			}
			stores[storename] = store
		return stores

	def get_all(self):
		return {
			"shopping_list":	self.get_shopping_list(),
			"items":			self.get_item_list(),
			"stores":			self.get_stores(),
		}

	def add_store(self, store_name):
		with contextlib.suppress(sqlite3.IntegrityError):
			self._cursor.execute("INSERT INTO stores (storename) VALUES (?);", (store_name, ))
			self._db.commit()
		return self._cursor.execute("SELECT storeid FROM stores WHERE storename = ?;", (store_name, )).fetchone()[0]

	def reset_store_order(self, storeid):
		self._cursor.execute("DELETE FROM storeitemorder WHERE storeid = ?", (storeid, ))
		self._db.commit()

	def set_store_order(self, storeid, item_orders):
		for (itemid, orderno) in sorted(item_orders.items()):
			self._cursor.execute("INSERT INTO storeitemorder (storeid, itemid, orderno) VALUES (?, ?, ?);", (storeid, itemid, orderno))
		self._db.commit()

	def add_item(self, item_name, commit = True):
		with contextlib.suppress(sqlite3.IntegrityError):
			self._cursor.execute("INSERT INTO items (description) VALUES (?);", (item_name, ))
			if commit:
				self._db.commit()
		return self._cursor.execute("SELECT itemid FROM items WHERE description = ?;", (item_name, )).fetchone()[0]

	def add_items(self, item_names):
		item_ids = { }
		for item_name in item_names:
			item_ids[item_name] = self.add_item(item_name, commit = False)
		self._db.commit()
		return item_ids

	def process_transaction(self, transactionid, itemid, delta, user):
		if delta == 0:
			# Discard
			return

		(count, ) = self._cursor.execute("SELECT COUNT(*) FROM history WHERE transactionid = ?;", (transactionid, )).fetchone()
		if count != 0:
			# Transaction already processed, discard.
			return

		# Transaction timestamp
		processed_utc = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

		# Get current value
		itemcount = self._cursor.execute("SELECT itemcount FROM shopping_list WHERE itemid = ?;", (itemid, )).fetchone()
		if itemcount is None:
			# Value is not in table at all.
			itemcount = 0
			self._cursor.execute("INSERT INTO shopping_list (itemid, itemcount, last_edited_utc) VALUES (?, ?, ?);", (itemid, 0, processed_utc))
		else:
			itemcount = itemcount[0]

		# Update item count
		self._cursor.execute("UPDATE shopping_list SET itemcount = itemcount + ?, last_edited_utc = ? WHERE itemid = ?;", (delta, processed_utc, itemid))

		# Insert transaction history item
		self._cursor.execute("INSERT INTO history (transactionid, itemid, delta, user, processed_utc) VALUES (?, ?, ?, ?, ?);", (transactionid, itemid, delta, user, processed_utc))
		self._db.commit()

if __name__ == "__main__":
	import uuid
	db = ShoppingListDB("pyslist.sqlite3")
	foo_item = db.add_item("Foo Item")
	db.process_transaction(str(uuid.uuid4()), itemid = foo_item, delta = 1, user = "joe")
	print(db.get_all())
