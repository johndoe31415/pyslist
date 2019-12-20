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

export function new_uuid4() {
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
