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
import json

class Configuration():
	def __init__(self, config_filename):
		self._config_filename = config_filename
		with open(self._config_filename) as f:
			self._config = json.load(f)
		self._install_dir = os.path.realpath(os.path.dirname(__file__))

	@classmethod
	def default(cls):
		install_dir = os.path.realpath(os.path.dirname(__file__))
		config_filename = install_dir + "/config.json"
		return cls(config_filename = config_filename)

	def _path_replace(self, path):
		path = path.replace("${INSTALL_DIR}", self._install_dir)
		return os.path.realpath(os.path.expanduser(path))

	@property
	def db_filename(self):
		return self._path_replace(self._config["database"])

if __name__ == "__main__":
	config = Configuration.default()
	print(config.db_filename)
