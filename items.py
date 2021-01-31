import sys
import traceback
import re
import mwparserfromhell as mw
import api
import util
import csv
from typing import *
import urllib.request

"this isn't quite right, because 2h, but the format isn't smart enough for that"
slotIDs: Dict[str, int] = {
	"weapon": 3,
	"2h": 3,
	"body": 4,
	"head": 0,
	"ammo": 13,
	"legs": 7,
	"feet": 10,
	"hands": 9,
	"cape": 1,
	"neck": 2,
	"ring": 12,
	"shield": 5
}

WEIGHT_REDUCTION_EXTRACTOR = re.compile(
	r"(?i)'''(?:In )?inventory:?''':? ([0-9.-]+) kg<br ?\/?> *'''Equipped:?''':? ([0-9.-]+)")


def getLimits():
	req = urllib.request.Request(
		'https://oldschool.runescape.wiki/w/Module:GELimits/data?action=raw', headers=api.user_agent)
	with urllib.request.urlopen(req) as response:
		data = response.read()
	limits = {}
	for line in data.splitlines():
		match = re.search(r"\[\"(.*)\"\] = (\d+),?", str(line))
		if match:
			name = match.group(1).replace('\\', '')
			limit = match.group(2)
			limits[name] = int(limit)
	return limits

def getCombatStyles():
	combatStyles = {}
	offset = 0
	while(True):
		req = urllib.request.Request(
			f'https://oldschool.runescape.wiki/w/Special:Ask/format=csv/sort=/order=asc/offset={offset}/limit=500/-5B-5BCombat-20style::+-5D-5D/-3FCombat-20style/mainlabel%3D/prettyprint=true/unescape=true/searchlabel=DCSV'
			, headers=api.user_agent
		)
		with urllib.request.urlopen(req) as response:
			data = response.read()
		csvString = data.decode("utf-8")
		lines = csvString.splitlines()
		reader = csv.reader(lines)
		for line in reader:
			itemName = line[0].split("#", 1)[0] # Remove variations, like (p), (p++) or degraded barrows gear. These will all be the same weapon style.
			weaponType = line[1]
			combatStyles[itemName] = weaponType
		if(len(lines) < 501):
			break
		offset += 500	

	return combatStyles


def run():
	limits = getLimits()
	combatStyles = getCombatStyles()
	stats = {}

	item_pages = api.query_category("Items")
	for name, page in item_pages.items():
		if name.startswith("Category:"):
			continue

		try:
			code = mw.parse(page, skip_style_tags=True)

			equips = {}
			for (vid, version) in util.each_version("Infobox Bonuses", code, include_base=True):
				doc = {}
				equips[vid] = doc

				if "slot" in version:
					slotID = str(version["slot"]).strip().lower()
					if slotID in slotIDs:
						doc["slot"] = slotIDs[slotID]
						if doc["slot"] == 3 and name in combatStyles:
							doc["combat_style"] = combatStyles[name]
						if slotID == "2h":
							doc["is2h"] = True
					elif slotID != "?":
						print("Item {} has unknown slot {}".format(name, slotID))

				for key in [
					"astab", "aslash", "acrush", "amagic", "arange", "dstab", "dslash", "dcrush", "dmagic", "drange", "str",
					"rstr", "mdmg", "prayer", ("speed", "aspeed")
				]:
					try:
						util.copy(key, doc, version, lambda x: int(x))
					except ValueError:
						print("Item {} has an non integer {}".format(name, key))

			for (vid, version) in util.each_version("Infobox Item", code, mergable_keys=None if len(equips) <= 1 else []):
				if "removal" in version and not str(version["removal"]).strip().lower() in ["", "no"]:
					continue

				doc = util.get_doc_for_id_string(name + str(vid), version, stats)
				if doc == None:
					continue

				util.copy("name", doc, version)
				if not "name" in doc:
					doc["name"] = name

				util.copy("quest", doc, version, lambda x: x.lower() != "no")

				equipable = "equipable" in version and "yes" in str(version["equipable"]).strip().lower()

				if "weight" in version:
					strval = str(version["weight"]).strip()
					if strval.endswith("kg"):
						strval = strval[:-2].strip()
					if strval != "":
						red = WEIGHT_REDUCTION_EXTRACTOR.match(strval)
						if red:
							strval = red.group(2)
						floatval = float(strval)
						if floatval != 0:
							doc["weight"] = floatval

				equipVid = vid if vid in equips else -1 if -1 in equips else None
				if equipVid != None:
					if equipable or not "broken" in version["name"].lower():
						if not equipable:
							print("Item {} has Infobox Bonuses but not equipable".format(name))
						doc["equipable"] = True
						doc["equipment"] = equips[equipVid]
				elif equipable:
					print("Item {} has equipable but not Infobox Bonuses".format(name))
					doc["equipable"] = True
					doc["equipment"] = {}

				itemName = name
				if "gemwname" in version:
					itemName = str(version["gemwname"]).strip()
				elif "name" in version:
					itemName = str(version["name"]).strip()
				if itemName in limits:
					doc['ge_limit'] = limits[itemName]

		except (KeyboardInterrupt, SystemExit):
			raise
		except:
			print("Item {} failed:".format(name))
			traceback.print_exc()

	util.write_json("stats.json", "stats.ids.min.json", stats)
