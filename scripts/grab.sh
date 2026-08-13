#!/bin/bash
u="$1"
f="pages/$(echo "$u" | sed 's|https://inbeat.agency/||; s|/|__|g; s|^$|HOME|').html"
curl -sS -A "Mozilla/5.0" --max-time 45 "$u" -o "$f"
