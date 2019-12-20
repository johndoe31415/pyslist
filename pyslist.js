/*
	pyslist - Python-based shopping list
	Copyright (C) 2019-2019 Johannes Bauer

	This file is part of pyslist.

	pyslist is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; this program is ONLY licensed under
	version 3 of the License, later versions are explicitly excluded.

	pyslist is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with pyslist; if not, write to the Free Software
	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

	Johannes Bauer <JohannesBauer@gmx.de>
*/

function hex(value, length) {
	value = Number(value).toString(16);
	while (value.length < length) {
		value = "0" + value;
	}
	return value;
}

function new_uuid4() {
	const bindata = [ ];
	for (let i = 0; i < 16; i++) {
		bindata[i] = (Math.random() * 256) | 0;
	};
	bindata[6] = (bindata[6] & 0x0f) | 0x40;
	bindata[8] = (bindata[8] & 0x3f) | 0x80;

	var string_uuid = "";
	for (let i = 0; i < 4; i++) {
		string_uuid += hex(bindata[i], 2);
	}
	string_uuid += "-";
	for (let i = 4; i < 6; i++) {
		string_uuid += hex(bindata[i], 2);
	}
	string_uuid += "-";
	for (let i = 6; i < 8; i++) {
		string_uuid += hex(bindata[i], 2);
	}
	string_uuid += "-";
	for (let i = 8; i < 10; i++) {
		string_uuid += hex(bindata[i], 2);
	}
	string_uuid += "-";
	for (let i = 10; i < 16; i++) {
		string_uuid += hex(bindata[i], 2);
	}
	return string_uuid;
}

export class ShoppingList {
	constructor(options) {
		this._options = options;
		this._base_api = "api.py";
		this._stores = null;
		this._items = null;
		this._id_by_item_name = null;
		this._shopping_list = null;
	}

	_get_sorted_shopping_list() {
		let sorted_shopping_list = [ ];
		if (this._shopping_list) {
			for (let itemid in this._shopping_list) {
				const item = {
					"itemid":	itemid | 0,
					"count":	this._shopping_list[itemid],
				};
				if ((this._items != null) && (item["itemid"] in this._items)) {
					item["name"] = this._items[item["itemid"]];
				} else {
					item["name"] = "Unknown (ID " + item["itemid"] + ")";
				}
				item["orderid"] = item["itemid"];
				sorted_shopping_list.push(item);

			}
		}

		sorted_shopping_list.sort((a, b) => (a["orderid"] < b["orderid"]));
		return sorted_shopping_list;
	}

	_display_shopping_list() {
		const div = this._options["shopping_list_div"];
		if (!div) {
			console.log("Cannot display, no DIV element given.");
			return;
		}

		const fragment = document.createDocumentFragment();
		const ul = document.createElement("tr");

		for (let item of this._get_sorted_shopping_list()) {
			let li = document.createElement("li");
			li.innerHTML = item.name;
			ul.append(li);
		}

		fragment.append(ul);

		div.innerHTML = "";
		div.append(fragment);

		console.log("show", this._options);
	}

	_store_data(data) {
		console.log("rx", data);
		if ("stores" in data) {
			this._stores = data["stores"];
		}
		if ("items" in data) {
			this._items = data["items"];
			this._id_by_item_name = { };
			for (var itemid in this._items) {
				itemid = itemid | 0;
				const itemname = this._items[itemid];
				this._id_by_item_name[itemname] = itemid;
			}
		}
		if ("shopping_list" in data) {
			this._shopping_list = data["shopping_list"];
			this._display_shopping_list();
		}
	}

	_dispatch(msg) {
		if (!msg["success"]) {
			console.log("Server returned error message", msg);
			return;
		}
		if (msg["msg"] == "all") {
			console.log(this, msg);
			this._store_data(msg["data"]);
		} else {
			console.log("Unhandled message type", msg);
		}
	}

	_async_fetch(endpoint, post_data, dispatcher) {
		const options = {
			"method":	post_data ? "post" : "get",
		};
		if (post_data) {
			options["body"] = JSON.stringify(post_data);
		}
		fetch(this._base_api + endpoint, options).then(function(response) {
			if (response.status == 200) {
				return response.json();
			} else {
				console.log("Error fetching " + endpoint + " (HTTP " + response.status + ").");
			}
		}).then((msg) => dispatcher ? dispatcher(msg) : this._dispatch(msg));
	}

	retrieve_initially() {
		this._async_fetch("/all");
	}

	_add_item_with_id(itemid, delta) {
		const transaction = {
			"itemid":			itemid,
			"delta":			delta,
			"transactionid":	new_uuid4(),
		};
		console.log(transaction);
	}

	add_item(item_name, confirmation_callback) {
		if (!(item_name in this._id_by_item_name)) {
			/* Item doesn't exist yet. Ask if we should create it. */
			if (!confirmation_callback(item_name)) {
				return;
			}

			this._async_fetch("/item", { "name": item_name }, (msg) => {
				/* Item was successfully created */
				console.log("item created", msg);
				this._add_item_with_id(0, 1);
			});
		} else {
			this._add_item_with_id(this._id_by_item_name["item_name"], 1);
		}
	}
}
