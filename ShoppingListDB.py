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
				itemid integer PRIMARY KEY,
				description varchar NOT NULL
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
				storeid integer PRIMARY KEY,
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
		self._cursor.execute("SELECT FROM shopping_list ")
		pass

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
	db = ShoppingListDB("example.sqlite3")
	db.process_transaction(str(uuid.uuid4()), 1, 1, "joe")
