import api

import items

api.use_cache = True

items.run()
'''
npc_info = []
npc_pages = query_category("Monsters")
for name, page in npc_pages.items():
	code = mw.parse(page, skip_style_tags=True)
	infoboxes = code.filter_templates(matches=lambda t: t.name.matches("Infobox Monster"))
	if len(infoboxes) < 1:
		print("Page {} has no Infobox Monsters".format(name))
	for infobox in infoboxes:
		infobox.
'''
