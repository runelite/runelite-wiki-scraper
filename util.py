import json
import collections
import re
import mwparserfromhell as mw
from typing import *

VERSION_EXTRACTOR = re.compile(r"(.*?)([0-9]+)?$")


def each_version(template_name: str, code, include_base: bool = False,
	mergable_keys: List[str] = None) -> Iterator[Tuple[int, Dict[str, Any]]]:
	"""
	each_version is a generator that yields each version of an infobox
	with variants, such as {{Infobox Item}} on [[Ring of charos]]
	"""
	if mergable_keys is None:
		mergable_keys = ["version", "image", "caption"]
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
			all_mergable = True
			for versionID, versionDict in versions.items():
				for key in versionDict:
					if not key in mergable_keys:
						all_mergable = False
			if all_mergable:
				yield (-1, base)
			else:
				if include_base:
					yield (-1, base)
				for versionID, versionDict in versions.items():
					yield (versionID, {**base, **versionDict})


def write_json(name: str, minName: str, docs: Dict[Any, Dict[str, Any]]):
	items = []
	for (id, doc) in docs.items():
		named = {k: v for (k, v) in doc.items() if not k.startswith("__")}
		nameless = named.copy()
		if "name" in nameless:
			del nameless["name"]
		if nameless != {}:
			items.append((id, named, nameless))
	items.sort(key=lambda k: int(k[0]))

	withNames = collections.OrderedDict([(k, v) for (k, v, _) in items])
	with open(name, "w+") as fi:
		json.dump(withNames, fi, indent=2)

	withoutNames = collections.OrderedDict([(k, v) for (k, _, v) in items])
	with open(minName, "w+") as fi:
		json.dump(withoutNames, fi, separators=(",", ":"))


def get_doc_for_id_string(source: str, version: Dict[str, str], docs: Dict[str, Dict],
	allow_duplicates: bool = False) -> Optional[Dict]:
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


def copy(name: Union[str, Tuple[str, str]],
	doc: Dict,
	version: Dict[str, Any],
	convert: Callable[[Any], Any] = lambda x: x) -> bool:
	src_name = name if isinstance(name, str) else name[0]
	dst_name = name if isinstance(name, str) else name[1]
	if not src_name in version:
		return False
	strval = str(version[src_name]).strip()
	if strval == "":
		return False
	newval = convert(strval)
	if not newval:
		return False
	doc[dst_name] = newval
	return True


def has_template(name: str, code) -> bool:
	return len(code.filter_templates(matches=lambda t: t.name.matches(name))) != 0
