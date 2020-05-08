# -*- coding: utf-8 -*-
from viur.core.bones import baseBone
from math import pow
from viur.core.bones.bone import ReadFromClientError, ReadFromClientErrorSeverity
import logging


class numericBone(baseBone):
	"""
		Holds numeric values.
		Can be used for ints and floats.
		For floats, the precision can be specified in decimal-places.
	"""

	@staticmethod
	def generageSearchWidget(target, name="NUMERIC BONE", mode="range"):
		return ({"name": name, "mode": mode, "target": target, "type": "numeric"})

	type = "numeric"

	def __init__(self, precision=0, min=-int(pow(2, 30)), max=int(pow(2, 30)), defaultValue = None, *args, **kwargs):
		"""
			Initializes a new NumericBone.

			:param precision: How may decimal places should be saved. Zero casts the value to int instead of float.
			:type precision: int
			:param min: Minimum accepted value (including).
			:type min: float
			:param max: Maximum accepted value (including).
			:type max: float
		"""
		super(numericBone, self).__init__(defaultValue=defaultValue, *args, **kwargs)
		self.precision = precision
		if not self.precision and "mode" in kwargs and kwargs["mode"] == "float":  # Fallback for old API
			self.precision = 8
		self.min = min
		self.max = max

	def fromClient(self, skel, name, data):
		"""
			Reads a value from the client.
			If this value is valid for this bone,
			store this value and return None.
			Otherwise our previous value is
			left unchanged and an error-message
			is returned.

			:param name: Our name in the skeleton
			:type name: str
			:param data: *User-supplied* request-data
			:type data: dict
			:returns: None or String
		"""
		if not name in data:
			return [ReadFromClientError(ReadFromClientErrorSeverity.NotSet, name, "Field not submitted")]
		rawValue = data[name]
		value = None
		if rawValue:
			try:
				rawValue = str(rawValue).replace(",", ".", 1)
			except:
				value = None
			else:
				if self.precision and (str(rawValue).replace(".", "", 1).replace("-", "", 1).isdigit()) and float(
						rawValue) >= self.min and float(rawValue) <= self.max:
					value = round(float(rawValue), self.precision)
				elif not self.precision and (str(rawValue).replace("-", "", 1).isdigit()) and int(
						rawValue) >= self.min and int(rawValue) <= self.max:
					value = int(rawValue)
				else:
					value = None
		if value is None:
			skel[name] = None
			return [ReadFromClientError(ReadFromClientErrorSeverity.Empty, name, "No value entered")]
		if value != value:  # NaN
			return [ReadFromClientError(ReadFromClientErrorSeverity.Invalid, name, "Invalid value entered")]
		err = self.isInvalid(value)
		if err:
			return [ReadFromClientError(ReadFromClientErrorSeverity.Invalid, name, err)]
		skel[name] = value


	def unserialize(self, skel, name):
		if name in skel.dbEntity:
			value = skel.dbEntity[name]
			isType = type(value)
			if self.precision:
				shouldType = float
			else:
				shouldType = int
			if isType == shouldType:
				skel.accessedValues[name] = value
			elif isType == int or isType == float:
				skel.accessedValues[name] = shouldType(value)
			elif isType == str and str(value).replace(".", "", 1).lstrip("-").isdigit():
				skel.accessedValues[name] = shouldType(value)
			else:
				return False
			return True
		return False

	def buildDBFilter(self, name, skel, dbFilter, rawFilter, prefix=None):
		updatedFilter = {}
		for parmKey, paramValue in rawFilter.items():
			if parmKey.startswith(name):
				if parmKey != name and not parmKey.startswith(name + "$"):
					# It's just another bone which name start's with our's
					continue
				try:
					if not self.precision:
						paramValue = int(paramValue)
					else:
						paramValue = float(paramValue)
				except ValueError:
					# The value we should filter by is garbage, cancel this query
					logging.warning("Invalid filtering! Unparsable int/float supplied to numericBone %s" % name)
					raise RuntimeError()
				updatedFilter[parmKey] = paramValue
		return super(numericBone, self).buildDBFilter(name, skel, dbFilter, updatedFilter, prefix)

	def getSearchDocumentFields(self, valuesCache, name, prefix=""):
		if isinstance(valuesCache.get(name), int) or isinstance(valuesCache.get(name), float):
			return [search.NumberField(name=prefix + name, value=valuesCache[name])]
		return []
