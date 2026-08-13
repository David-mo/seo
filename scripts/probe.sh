#!/bin/bash
u="$1"
resp=$(curl -sS -A "Mozilla/5.0" -D - -o /tmp/b.$$ -w "\nSTATUS:%{http_code}\nLOC:%{redirect_url}\n" "$u")
code=$(echo "$resp" | grep '^STATUS:' | cut -d: -f2)
loc=$(echo "$resp" | grep '^LOC:' | cut -d: -f2-)
canon=$(grep -o '<link[^>]*rel="canonical"[^>]*>' /tmp/b.$$ | head -1 | grep -o 'href="[^"]*"' | cut -d'"' -f2)
title=$(tr '\n' ' ' < /tmp/b.$$ | grep -o '<title>[^<]*' | head -1 | sed 's/<title>//')
rm -f /tmp/b.$$
echo -e "$code\t$u\t$loc\t$canon\t$title"
