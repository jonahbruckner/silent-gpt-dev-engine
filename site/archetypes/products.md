+++
title       = "{{ replace .Name "-" " " | title }}"
slug        = "{{ .Name }}"
date        = "{{ .Date }}"

# 1-Satz-Tagline
description = "A curated bundle of SilentGPT micro-tutorials on …"

# 2–3 Sätze Hero-Text – bitte nach dem Anlegen anpassen
hero_body = """
Describe who this pack is for, what problem it solves and what kind of content it contains.
Aim for two or three concise sentences, focused on concrete benefits.
"""

pack_slug   = "{{ .Name }}"
price_label = "9,99 €"
type        = "products"
+++

