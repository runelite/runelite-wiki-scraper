import json
import collections
import re
import mwparserfromhell as mw
from typing import *

VERSION_EXTRACTOR = re.compile(r"(.*?)([0-9]+)?$")


def each_version(template_name: str, code) -> Iterator[Tuple[int, Dict[str, Any]]]:
	"""
	each_version is a generator that yields each version of an infobox
	with variants, such as {{Infobox Item}} on [[Ring of charos]]
	"""
	infoboxes = code.filter_templates(matches=lambda t: t.name.matches(template_name))
	if len(infoboxes) < 1:
		return
	for infobox in infoboxes:
		base: Dict[str, str] = {}
		versions: Dict[int, Dict[str, str]] = {}
		for param in infobox.params:
			matcher = VERSION_EXTRACTOR.match(str(param.name).strip())
			if matcher is None:
				raise AssertionError()
			primary = matcher.group(1)
			dic = base
			if matcher.group(2) != None:
				version = int(matcher.group(2))
				if not version in versions:
					versions[version] = {}
				dic = versions[version]
			dic[primary] = param.value
		if len(versions) == 0:
			yield (-1, base)
		else:
			for versionID, versionDict in versions.items():
				yield (versionID, {**base, **versionDict})


def write_json(name: str, minName: str, doc: Dict):
	orderedStats = collections.OrderedDict(
		sorted(filter(lambda e: e[1] != {},
		map(lambda e: (e[0], dict(filter(lambda k: not k[0].startswith("__"), e[1].items()))), doc.items())),
		key=lambda k: int(k[0])))

	with open(name, "w+") as fi:
		json.dump(orderedStats, fi, indent=2)

	with open(minName, "w+") as fi:
		json.dump(orderedStats, fi, separators=(",", ":"))


def get_doc_for_id_string(source: str, version: Dict[str, str], docs: Dict[str, Dict], allow_duplicates: bool = False) -> Optional[Dict]:
	if not "id" in version:
		print("page {} is missing an id".format(source))
		return None

	ids = [id for id in map(lambda id: id.strip(), str(version["id"]).split(",")) if id != "" and id.isdigit()]

	if len(ids) == 0:
		print("page {} is has an empty id".format(source))
		return None

	doc = {}
	doc["__source__"] = source
	invalid = False
	for id in ids:
		if not allow_duplicates and id in docs:
			print("page {} is has the same id as {}".format(source, docs[id]["__source__"]))
			invalid = True
		docs[id] = doc

	if invalid:
		return None
	return doc


def copy(name: str, doc: Dict, version: Dict[str, Any], convert: Callable[[Any], Any]) -> bool:
	if not name in version:
		return False
	strval = str(version[name]).strip()
	if strval == "":
		return False
	newval = convert(strval)
	if not newval:
		return False
	doc[name] = newval
	return True