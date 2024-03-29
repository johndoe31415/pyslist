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

import { new_uuid4 } from './uuid.js';

function cmpvalue(a, b) {
	if (a == b) {
		return 0;
	} else if (a < b) {
		return -1;
	} else {
		return 1;
	}
}

export class ShoppingList {
	constructor(options) {
		this._options = options;
		this._base_api = "api.py";
		this._stores = null;
		this._items = null;
		this._id_by_item_name = null;
		this._shopping_list = null;
		this._autocomplete = null;
	}

	_get_sorted_shopping_list() {
		let sort_order = null;
		if (this._options["sort_order_combobox"]) {
			const sort_order_value = this._options["sort_order_combobox"].value;
			if ((this._stores) && (sort_order_value in this._stores)) {
				sort_order = this._stores[sort_order_value].order;
			}
		}

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
				if (sort_order == null) {
					item["orderid"] = item["name"].toLowerCase();
				} else {
					item["orderid"] = sort_order[item["itemid"]] || -1;
					if (item["orderid"] == -1) {
						item["orderid"] = 9999999;
					}
				}

				if (item.count > 0) {
					sorted_shopping_list.push(item);
				}
			}
		}

		sorted_shopping_list.sort((a, b) => cmpvalue(a["orderid"], b["orderid"]) || cmpvalue(a["name"], b["name"]));
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

			{
				const button = document.createElement("button");
				button.innerHTML = "-";
				button.addEventListener("click", (event) => {
					this._add_item_with_id(item["itemid"], -1);
				});
				li.append(button);
			}
			{
				const button = document.createElement("button");
				button.innerHTML = "+";
				button.addEventListener("click", (event) => {
					this._add_item_with_id(item["itemid"], 1);
				});
				li.append(button);
			}
			{
				const span = document.createElement("span");
				const item_display = (item.count == 1) ? item.name : item.count + " x " + item.name;
				span.innerHTML = item_display;
				li.append(span);
			}

			ul.append(li);
		}

		fragment.append(ul);

		div.innerHTML = "";
		div.append(fragment);

	}

	_populate_store_combobox() {
		if (!this._options["sort_order_combobox"]) {
			console.log("No sort order combobox available, not populating.");
			return;
		}

		const combo = this._options["sort_order_combobox"];
		for (var i = 1; i < combo.children.length; i++) {
			combo.children[i].remove();
		}

		for (var storename in this._stores) {
			const store = this._stores[storename];

			const option = document.createElement("option");
			option.value = storename;
			option.innerHTML = storename;
			combo.append(option);
		}
	}

	_store_data(data) {
		if ("stores" in data) {
			this._stores = data["stores"];
			this._populate_store_combobox();
		}
		if ("items" in data) {
			this._items = data["items"];
			this._id_by_item_name = { };
			this._autocomplete = [ ];
			for (var itemid in this._items) {
				itemid = itemid | 0;
				const itemname = this._items[itemid];
				this._id_by_item_name[itemname] = itemid;
				this._autocomplete.push(itemname);
			}
			this._autocomplete.sort();
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
			this._store_data(msg["data"]);
		} else if (msg["msg"] == "transaction") {
			/* Ignore */
		} else {
			console.log("Unhandled message type", msg);
		}
	}

	_async_fetch(endpoint, post_data, dispatcher, retry_delay_secs) {
		const options = {
			"method":	post_data ? "post" : "get",
		};
		if (post_data) {
			options["body"] = JSON.stringify(post_data);
		}
		fetch(this._base_api + endpoint, options).then((response) => {
			if (response.status == 200) {
				return response.json();
			} else {
				console.log("Error fetching " + endpoint + " (HTTP " + response.status + "), retry " + retry_delay_secs + ".");
				if (retry_delay_secs) {
					setTimeout(() => this._async_fetch(endpoint, post_data, dispatcher, retry_delay_secs), 1000 * retry_delay_secs);
				}
				return null;
			}
		}).then((msg) => {
			if (msg) {
				if (dispatcher) {
					dispatcher(msg);
				} else {
					this._dispatch(msg);
				}
			}
		}).catch((exception) => {
			console.log("Caught exception:", exception, "Retry:", retry_delay_secs);
			if (retry_delay_secs) {
				setTimeout(() => this._async_fetch(endpoint, post_data, dispatcher, retry_delay_secs), 1000 * retry_delay_secs);
			}
		});
	}

	retrieve_initially() {
		this._async_fetch("/all", null, null, 2.0);
	}

	_execute_transaction(transaction) {
		this._async_fetch("/transaction", transaction, null, 2.0);
	}

	_add_item_with_id(itemid, delta) {
		const transaction = {
			"itemid":			itemid,
			"delta":			delta,
			"transactionid":	new_uuid4(),
		};
		if (!(itemid in this._shopping_list)) {
			this._shopping_list[itemid] = 0;
		}
		this._shopping_list[itemid] += delta;
		this._display_shopping_list();
		this._execute_transaction(transaction);
	}

	add_item(item_name, confirmation_callback) {
		if (!(item_name in this._id_by_item_name)) {
			/* Item doesn't exist yet. Ask if we should create it. */
			if (!confirmation_callback(item_name)) {
				return;
			}

			this._async_fetch("/item", { "name": item_name }, (msg) => {
				/* Item was successfully created */
				const itemid = msg["itemid"];
				this._items[itemid] = item_name;
				this._id_by_item_name[item_name] = itemid;
				this._add_item_with_id(itemid, 1);
			});
		} else {
			this._add_item_with_id(this._id_by_item_name[item_name], 1);
		}
	}

	sort_order_changed() {
		this._display_shopping_list();
	}

	attempt_autocomplete(term, suggest) {
		if (this._autocomplete == null) {
			return;
		}

		term = term.toLowerCase();
		var matches = [ ];
		for (let i = 0; i < this._autocomplete.length; i++) {
			if (this._autocomplete[i].toLowerCase().indexOf(term) == 0) {
				matches.push(this._autocomplete[i]);
			}
		}
		matches.sort();
		suggest(matches);
	}
}
