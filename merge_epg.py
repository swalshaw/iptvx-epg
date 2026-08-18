#!/usr/bin/env python3

import urllib.request
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCES = [
    "https://epgshare01.online/epgshare01/epg_ripper_NZ1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz",
]

OUTPUT_DIR = Path("public")
XML_OUTPUT = OUTPUT_DIR / "epg.xml"
GZ_OUTPUT = OUTPUT_DIR / "epg.xml.gz"

OUTPUT_DIR.mkdir(exist_ok=True)

root_out = ET.Element(
    "tv",
    {
        "generator-info-name": "IPTVX NZ AU UK EPG",
        "source-info-name": "Merged EPG"
    }
)

seen_channels = set()
seen_programmes = set()

for url in SOURCES:
    print(f"Downloading {url}")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 IPTVX-EPG"}
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        with gzip.GzipFile(fileobj=response) as gz:
            tree = ET.parse(gz)

    root = tree.getroot()

    added_channels = 0
    added_programmes = 0

    for channel in root.findall("channel"):
        channel_id = channel.get("id")

        if channel_id and channel_id not in seen_channels:
            seen_channels.add(channel_id)
            root_out.append(channel)
            added_channels += 1

    for programme in root.findall("programme"):
        channel = programme.get("channel", "")
        start = programme.get("start", "")
        stop = programme.get("stop", "")

        title_element = programme.find("title")
        title = (
            title_element.text
            if title_element is not None and title_element.text
            else ""
        )

        key = (channel, start, stop, title)

        if key not in seen_programmes:
            seen_programmes.add(key)
            root_out.append(programme)
            added_programmes += 1

    print(
        f"Added {added_channels} channels "
        f"and {added_programmes} programmes"
    )

tree_out = ET.ElementTree(root_out)

print("Writing XML...")
tree_out.write(
    XML_OUTPUT,
    encoding="utf-8",
    xml_declaration=True
)

print("Compressing XML...")

with open(XML_OUTPUT, "rb") as source:
    with gzip.open(GZ_OUTPUT, "wb", compresslevel=6) as destination:
        while True:
            chunk = source.read(1024 * 1024)

            if not chunk:
                break

            destination.write(chunk)

print()
print(f"Channels:   {len(seen_channels)}")
print(f"Programmes: {len(seen_programmes)}")
print(f"Created:    {XML_OUTPUT}")
print(f"Created:    {GZ_OUTPUT}")
