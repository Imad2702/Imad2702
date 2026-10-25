"""Rewrite the merged-PR block in README.md with PRs merged into other people's repos."""
import html
import json
import os
import re
import urllib.parse
import urllib.request

USER = os.environ.get("GH_USER", "Imad2702")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
SHOW = 10
README = "README.md"


def search(query: str, per_page: int = 100) -> dict:
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
        {"q": query, "sort": "updated", "order": "desc", "per_page": per_page}
    )
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def repo_name(item: dict) -> str:
    return item["repository_url"].split("/repos/")[-1]


def build_block() -> str:
    base = f"author:{USER} type:pr -user:{USER}"
    total = search(base, per_page=1)["total_count"]
    merged = search(base + " is:merged")
    items = merged["items"]
    merged_total = merged["total_count"]
    items.sort(key=lambda i: i["pull_request"].get("merged_at") or "", reverse=True)

    rows = []
    for it in items[:SHOW]:
        title = html.escape(it["title"])
        repo = html.escape(repo_name(it))
        rows.append(
            f"""
<tr>
<td>

 **{title}** <br><sub>{repo}</sub>

</td>

<td align="right">
<a href="{it['html_url']}">
<img src="https://img.shields.io/badge/VIEW-7AA2F7?style=flat-square&logo=github&logoColor=1a1b27" />
</a>
</td>
</tr>
"""
        )

    shown = min(SHOW, len(items))
    return f"""<!--START_MERGED_PRS-->
<div align="center">

**🔀 {total} Total PRs**
&nbsp;&nbsp; • &nbsp;&nbsp;
**🟢 {merged_total} Merged PRs**

</div>

<table width="100%">
{''.join(rows)}
</table>

<div align="center">

<sub>
Showing latest {shown} of {merged_total} merged pull requests to other projects
&nbsp; • &nbsp;
<a href="https://github.com/pulls?q=is%3Amerged+is%3Apr+author%3A{USER}+-user%3A{USER}">see all</a>
</sub>

</div>
<!--END_MERGED_PRS-->"""


def main() -> None:
    with open(README, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(r"<!--START_MERGED_PRS-->.*?<!--END_MERGED_PRS-->", re.S)
    if not pattern.search(text):
        raise SystemExit("Markers not found in README.md")
    new_text = pattern.sub(lambda _: build_block(), text)
    if new_text != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new_text)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
