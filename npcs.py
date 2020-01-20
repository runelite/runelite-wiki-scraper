import traceback
import re
import mwparserfromhell as mw
import api
import util
from typing import *

def run():
    npcs = {}

    item_pages = api.query_category("Monsters")
    for name, page in item_pages.items():
        if name.startswith("Category:"):
            continue

        try:
            code = mw.parse(page, skip_style_tags=True)

            for (vid, version) in util.each_version("Infobox Monster", code):
                doc = util.get_doc_for_id_string(name + str(vid), version, npcs)
                if doc == None:
                    continue
                for key in ["name", "hitpoints", "combat"]:
                    util.copy(key, doc, version, lambda x: x)

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print("NPC {} failed:".format(name))
            traceback.print_exc()

    util.write_json("npcs.json", "npcs.min.json", npcs)
