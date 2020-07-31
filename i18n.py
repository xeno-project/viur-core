# -*- coding: utf-8 -*-

from viur.core.utils import currentRequest, currentLanguage
from viur.core.config import conf
from viur.core import db
from jinja2.ext import Extension, nodes
from datetime import datetime

systemTranslations = {}


class translate:
	__slots__ = ["key", "defaultText", "hint", "translationCache"]

	def __init__(self, key, defaultText=None, hint=None):
		super(translate, self).__init__()
		self.key = key.lower()
		self.defaultText = defaultText
		self.hint = hint
		self.translationCache = None

	def __repr__(self):
		return "<translate object for %s>" % self.key

	def __str__(self):
		if self.translationCache is None:
			global systemTranslations
			self.translationCache = systemTranslations.get(self.key, {})
		try:
			lang = currentRequest.get().language
		except:
			return self.defaultText or self.key
		if lang in conf["viur.languageAliasMap"]:
			lang = conf["viur.languageAliasMap"][lang]
		if not lang in self.translationCache:
			return self.defaultText or self.key
		trStr = self.translationCache.get(lang, "")
		return trStr

	def translate(self, **kwargs):
		res = str(self)
		for k, v in kwargs.items():
			res = res.replace("{{%s}}" % k, str(v))
		return res


class TranslationExtension(Extension):
	tags = {"translate"}

	def parse(self, parser):
		# Parse the translate tag
		global systemTranslations
		args = []
		kwargs = {}
		lineno = parser.stream.current.lineno
		# Parse arguments (args and kwargs) until the current block ends
		while parser.stream.current.type != 'block_end':
			lastToken = parser.parse_expression()
			if parser.stream.current.type == "comma":  # It's an arg
				args.append(lastToken.value)
				next(parser.stream)  # Advance pointer
				continue
			elif parser.stream.current.type == "assign":
				next(parser.stream)  # Advance beyond =
				expr = parser.parse_expression()
				kwargs[lastToken.name] = expr.value
				if parser.stream.current.type == "comma":
					next(parser.stream)
				elif parser.stream.current.type == "block_end":
					break
				else:
					raise SyntaxError()
		if not 0 < len(args) < 3:
			raise SyntaxError("Translation-Key missing!")
		args += [""] * (3 - len(args))
		args += [kwargs]
		trKey = args[0]
		trDict = systemTranslations.get(trKey, {})
		args = [nodes.Const(x) for x in args]
		args.append(nodes.Const(trDict))
		return nodes.CallBlock(self.call_method("_translate", args), [], [], []).set_lineno(lineno)

	def _translate(self, key, defaultText, hint, kwargs, trDict, caller):
		# Perform the actual translation during render
		lng = currentLanguage.get()
		if lng in trDict:
			return trDict[lng].format(kwargs)
		return str(defaultText).format(kwargs)


def initializeTranslations():
	global systemTranslations
	invertMap = {}
	for srcLang, dstLang in conf["viur.languageAliasMap"].items():
		if dstLang not in invertMap:
			invertMap[dstLang] = []
		invertMap[dstLang].append(srcLang)
	for tr in db.Query("viur-translations").run(9999):
		trDict = {}
		for lang, translation in tr["translations"].items():
			trDict[lang] = translation
			if lang in invertMap:
				for v in invertMap[lang]:
					trDict[v] = translation
		systemTranslations[tr["key"]] = trDict


localizedDateTime = translate("const_datetimeformat", "%a %b %d %H:%M:%S %Y", "Localized Time and Date format string")
localizedDate = translate("const_dateformat", "%m/%d/%Y", "Localized Date only format string")
localizedTime = translate("const_timeformat", "%H:%M:%S", "Localized Time only format string")
localizedAbbrevDayNames = {
	0: translate("const_day_0_short", "Sun", "Abbreviation for Sunday"),
	1: translate("const_day_1_short", "Mon", "Abbreviation for Monday"),
	2: translate("const_day_2_short", "Tue", "Abbreviation for Tuesday"),
	3: translate("const_day_3_short", "Wed", "Abbreviation for Wednesday"),
	4: translate("const_day_4_short", "Thu", "Abbreviation for Thursday"),
	5: translate("const_day_5_short", "Fri", "Abbreviation for Friday"),
	6: translate("const_day_6_short", "Sat", "Abbreviation for Saturday"),
}
localizedDayNames = {
	0: translate("const_day_0_long", "Sunday", "Sunday"),
	1: translate("const_day_1_long", "Monday", "Monday"),
	2: translate("const_day_2_long", "Tuesday", "Tuesday"),
	3: translate("const_day_3_long", "Wednesday", "Wednesday"),
	4: translate("const_day_4_long", "Thursday", "Thursday"),
	5: translate("const_day_5_long", "Friday", "Friday"),
	6: translate("const_day_6_long", "Saturday", "Saturday"),
}
localizedAbbrevMonthNames = {
	1: translate("const_month_1_short", "Jan", "Abbreviation for January"),
	2: translate("const_month_2_short", "Feb", "Abbreviation for February"),
	3: translate("const_month_3_short", "Mar", "Abbreviation for March"),
	4: translate("const_month_4_short", "Apr", "Abbreviation for April"),
	5: translate("const_month_5_short", "May", "Abbreviation for May"),
	6: translate("const_month_6_short", "Jun", "Abbreviation for June"),
	7: translate("const_month_7_short", "Jul", "Abbreviation for July"),
	8: translate("const_month_8_short", "Aug", "Abbreviation for August"),
	9: translate("const_month_9_short", "Sep", "Abbreviation for September"),
	10: translate("const_month_10_short", "Oct", "Abbreviation for October"),
	11: translate("const_month_11_short", "Nov", "Abbreviation for November"),
	12: translate("const_month_12_short", "Dec", "Abbreviation for December"),
}
localizedMonthNames = {
	1: translate("const_month_1_long", "January", "January"),
	2: translate("const_month_2_long", "February", "February"),
	3: translate("const_month_3_long", "March", "March"),
	4: translate("const_month_4_long", "April", "April"),
	5: translate("const_month_5_long", "May", "May"),
	6: translate("const_month_6_long", "June", "June"),
	7: translate("const_month_7_long", "July", "July"),
	8: translate("const_month_8_long", "August", "August"),
	9: translate("const_month_9_long", "September", "September"),
	10: translate("const_month_10_long", "October", "October"),
	11: translate("const_month_11_long", "November", "November"),
	12: translate("const_month_12_long", "December", "December"),
}
def localizedStrfTime(datetimeObj: datetime, format: str) -> str:
	"""
	Provides correct localized names for directives like %a which dont get translated on GAE properly as we can't
	set the locale (for each request).
	This currently replaces %a, %A, %b, %B, %c, %x and %X.

	:param datetimeObj: Datetime-instance to call strftime on
	:param format: String containing the Format to apply.
	:returns: Date and time formatted according to format with correct localization
	"""
	if "%c" in format:
		format = format.replace("%c", str(localizedDateTime))
	if "%x" in format:
		format = format.replace("%x", str(localizedDate))
	if "%X" in format:
		format = format.replace("%X", str(localizedTime))
	if "%a" in format:
		format = format.replace("%a", str(localizedAbbrevDayNames[int(datetimeObj.strftime("%w"))]))
	if "%A" in format:
		format = format.replace("%A", str(localizedDayNames[int(datetimeObj.strftime("%w"))]))
	if "%b" in format:
		format = format.replace("%b", str(localizedAbbrevMonthNames[int(datetimeObj.strftime("%m"))]))
	if "%B" in format:
		format = format.replace("%B", str(localizedMonthNames[int(datetimeObj.strftime("%m"))]))
	return datetimeObj.strftime(format)
