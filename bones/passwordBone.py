# -*- coding: utf-8 -*-
from viur.core import utils
from viur.core.bones import stringBone
from hashlib import sha256
import hmac
from struct import Struct
from operator import xor
from itertools import starmap
from viur.core.config import conf
import string, random
import codecs
from viur.core.bones.bone import ReadFromClientError, ReadFromClientErrorSeverity
from viur.core.i18n import translate


def pbkdf2(password, salt, iterations=1001, keylen=42):
	"""
		An implementation of PBKDF2 (http://wikipedia.org/wiki/PBKDF2)
		
		Mostly based on the implementation of 
		https://github.com/mitsuhiko/python-pbkdf2/blob/master/pbkdf2.py
		
		:copyright: (c) Copyright 2011 by Armin Ronacher.
		:license: BSD, see LICENSE for more details.
	"""
	_pack_int = Struct('>I').pack
	if isinstance(password, str):
		password = password.encode("UTF-8")
	if isinstance(salt, str):
		salt = salt.encode("UTF-8")
	mac = hmac.new(password, None, sha256)

	def _pseudorandom(x, mac=mac):
		h = mac.copy()
		h.update(x)
		return h.digest()

	buf = []
	for block in range(1, -(-keylen // mac.digest_size) + 1):
		rv = u = _pseudorandom(salt + _pack_int(block))
		for i in range(iterations - 1):
			u = _pseudorandom((''.join(map(chr, u))).encode("LATIN-1"))
			rv = starmap(xor, zip(rv, u))
		buf.extend(rv)
	return codecs.encode(''.join(map(chr, buf))[:keylen].encode("LATIN-1"), 'hex_codec')


class passwordBone(stringBone):
	"""
		A bone holding passwords.
		This is always empty if read from the database.
		If its saved, its ignored if its values is still empty.
		If its value is not empty, its hashed (with salt) and only the resulting hash 
		will be written to the database
	"""
	type = "password"
	saltLength = 13
	minPasswordLength = 8
	passwordTests = [
		lambda val: val.lower() != val,  # Do we have upper-case characters?
		lambda val: val.upper() != val,  # Do we have lower-case characters?
		lambda val: any([x in val for x in "0123456789"]),  # Do we have any digits?
		lambda val: any([x not in (string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in val]),
		# Special characters?
	]
	passwordTestThreshold = 3
	tooShortMessage = translate("server.bones.passwordBone.tooShortMessage",
								defaultText="The entered password is to short - it requires at least {{length}} characters.")
	tooWeakMessage = translate("server.bones.passwordBone.tooWeakMessage",
								defaultText="The entered password is too weak.")

	def isInvalid(self, value):
		if not value:
			return False

		if len(value) < self.minPasswordLength:
			return self.tooShortMessage.translate(length=self.minPasswordLength)

		# Run our password test suite
		testResults = []
		for test in self.passwordTests:
			testResults.append(test(value))

		if sum(testResults) < self.passwordTestThreshold:
			return str(self.tooWeakMessage)

		return False

	def fromClient(self, skel, name, data):
		if not name in data:
			return [ReadFromClientError(ReadFromClientErrorSeverity.NotSet, name, "Field not submitted")]
		value = data.get(name)
		if not value:
			# Password-Bone is special: As it cannot be read don't set back no None if no value is given
			# This means an once set password can only be changed - but never deleted.
			return [ReadFromClientError(ReadFromClientErrorSeverity.Empty, name, "No value entered")]
		err = self.isInvalid(value)
		if err:
			return [ReadFromClientError(ReadFromClientErrorSeverity.Invalid, name, err)]
		skel[name] = value

	def serialize(self, skel, name):
		if name in skel.accessedValues and skel.accessedValues[name]:
			salt = utils.generateRandomString(self.saltLength)
			passwd = pbkdf2(skel.accessedValues[name][: conf["viur.maxPasswordLength"]], salt)
			skel.dbEntity[name] = {"pwhash": passwd, "salt": salt}
			return True
		return False

	def unserialize(self, skeletonValues, name):
		return False
