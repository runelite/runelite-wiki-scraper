import re

VERSION_EXTRACTOR = re.compile(r"(.*?)([0-9]+)?$")

def each_version(template_name, code):
	"""
	each_version is a generator that yields each version of an infobox
	with variants, such as {{Infobox Item}} on [[Ring of charos]]
	"""
	infoboxes = code.filter_templates(
		matches=lambda t: t.name.matches(template_name))
	if len(infoboxes) < 1:
		return
	for infobox in infoboxes:
		base = {}
		versions = {}
		for param in infobox.params:
			matcher = VERSION_EXTRACTOR.match(str(param.name).strip())
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
			for versionID, version in versions.items():
				yield (versionID, {**base, **version})