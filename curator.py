#!/usr/bin/env python3
"""
GitHub Awesome Curator
======================
Lightweight, zero-dependency script to curate top-tier, trending GitHub repositories 
created or active from 2024 onwards across various domains.

Generates:
1. README.md (Formatted Awesome List with Markdown tables and jump links)
2. curated_repos.json (Raw JSON data for programmatic use)

Author: BenSnn & Antigravity
License: MIT
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

# Windows terminal UTF-8 encoding safeguard
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DEFAULT_CATEGORIES = [
    {
        "id": "ai-agents",
        "name": "🤖 AI, LLMs & Autonomous Agents",
        "description": "Cutting-edge artificial intelligence, large language model frameworks, autonomous agent architectures, and local inference engines.",
        "query": "created:>=2024-01-01 topic:ai stars:>500"
    },
    {
        "id": "cybersecurity",
        "name": "🛡️ Cyber Security, Pentesting & Forensics",
        "description": "Security testing tools, vulnerability scanners, packet analysis, defense utilities, and network forensic suites.",
        "query": "created:>=2024-01-01 topic:security stars:>100"
    },
    {
        "id": "devtools-cli",
        "name": "⚡ Developer Tools & Modern CLI",
        "description": "Terminal emulators, modern CLI utilities, high-performance developer ergonomics, and system productivity tools.",
        "query": "created:>=2024-01-01 topic:cli stars:>200"
    },
    {
        "id": "devops-monitoring",
        "name": "📊 DevOps, Cloud & Infrastructure",
        "description": "Log parsers, real-time monitoring daemons, containerization tools, microservice orchestrators, and CI/CD pipelines.",
        "query": "created:>=2024-01-01 topic:devops stars:>100"
    },
    {
        "id": "web-backend",
        "name": "🌐 Modern Web & High-Performance Backends",
        "description": "Fast web frameworks, asynchronous backend servers, API tooling, and lightweight web architectures.",
        "query": "created:>=2024-01-01 topic:backend stars:>200"
    }
]

def fetch_github_search(query: str, per_page: int = 10, token: str = None, retries: int = 2) -> list:
    """Fetch repositories using the GitHub Search API with automatic rate-limit backoff."""
    encoded_query = urllib.parse.quote(query, safe=":=><+")
    url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={per_page}"
    headers = {
        "User-Agent": "Awesome-Curator-Agent/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"
        
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("items", [])
        except urllib.error.HTTPError as e:
            if e.code == 403 and attempt < retries:
                reset_ts = e.headers.get("X-RateLimit-Reset")
                if reset_ts:
                    wait_time = max(2, int(float(reset_ts) - time.time()) + 2)
                    print(f"    [!] Search rate limit reached. Waiting {wait_time}s for reset window...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            print(f"[!] HTTP Error {e.code}: {e.reason} for query: {query}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"[!] Error fetching query: {e}", file=sys.stderr)
            return []
    return []

def format_number(n: int) -> str:
    """Format integers with commas for cleaner readability."""
    return f"{n:,}" if n is not None else "0"

def clean_description(desc: str) -> str:
    """Sanitize description for Markdown table cells."""
    if not desc:
        return "No description provided."
    # Remove pipes and newlines that break Markdown tables
    desc = desc.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()
    if len(desc) > 130:
        desc = desc[:127] + "..."
    return desc

def generate_markdown(curated_data: dict, author: str = "BenSnn") -> str:
    """Produce a high quality, aesthetic Markdown document."""
    total_repos = sum(len(cat["repos"]) for cat in curated_data["categories"])
    now_str = datetime.now().strftime("%Y-%m-%d")
    
    md = [
        f"# 🚀 Awesome Curated Vault (2024 - Present)",
        "",
        f"[![Total Repos](https://img.shields.io/badge/Curated_Repos-{total_repos}-brightgreen.svg)](#)",
        f"[![Updated](https://img.shields.io/badge/Updated-{now_str}-blue.svg)](#)",
        f"[![Curated By](https://img.shields.io/badge/Curated_By-@{author}-blueviolet.svg)](https://github.com/{author})",
        f"[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)",
        "",
        "> A hand-crafted, automated curation of the most outstanding, trending, and useful open-source repositories created from **2024 onwards**.",
        "",
        "---",
        "",
        "## 📑 Table of Contents",
        ""
    ]
    
    for cat in curated_data["categories"]:
        md.append(f"- [{cat['name']}](#{cat['id']}) (`{len(cat['repos'])} repositories`)")
    
    md.extend([
        "- [Contribution & Suggestions](#-contribution--suggestions)",
        "- [License](#-license)",
        "",
        "---",
        ""
    ])
    
    for cat in curated_data["categories"]:
        md.append(f"<a name=\"{cat['id']}\"></a>")
        md.append(f"## {cat['name']}")
        md.append(f"*{cat['description']}*")
        md.append("")
        
        if not cat["repos"]:
            md.append("> *No repositories found in this category yet.*")
            md.append("")
            continue
            
        md.append("| Repository | Stars | Language | Description |")
        md.append("| :--- | :---: | :---: | :--- |")
        
        for repo in cat["repos"]:
            name = repo["full_name"]
            url = repo["html_url"]
            stars = format_number(repo["stargazers_count"])
            lang = repo["language"] or "Unknown"
            desc = clean_description(repo["description"])
            
            md.append(f"| [**{name}**]({url}) | ⭐ {stars} | `{lang}` | {desc} |")
            
        md.append("")
        md.append("[⬆ Back to Top](#-table-of-contents)")
        md.append("")
        md.append("---")
        md.append("")
        
    md.extend([
        "## 🤝 Contribution & Suggestions",
        "",
        "Found an awesome repository from 2024+ that deserves to be on this list?",
        "1. Fork this repository.",
        "2. Add the tool to the appropriate section or update the curation script.",
        "3. Submit a Pull Request!",
        "",
        "## 📄 License",
        "",
        "This collection and curation script are licensed under the [MIT License](LICENSE).",
        ""
    ])
    
    return "\n".join(md)

def run_curator(limit_per_cat: int = 6, token: str = None, author: str = "BenSnn"):
    print(f"[*] Starting Awesome Curator for @{author}...")
    print(f"[*] Fetching up to {limit_per_cat} repos per category (Created >= 2024-01-01)...")
    
    seen_repos = set()
    output_data = {
        "curated_by": author,
        "generated_at": datetime.now().isoformat(),
        "categories": []
    }
    
    for idx, cat in enumerate(DEFAULT_CATEGORIES):
        print(f"\n[+] Processing [{idx+1}/{len(DEFAULT_CATEGORIES)}]: {cat['name']}")
        items = fetch_github_search(cat["query"], per_page=limit_per_cat * 2, token=token)
        
        selected_repos = []
        for item in items:
            if item["id"] in seen_repos:
                continue
            seen_repos.add(item["id"])
            selected_repos.append({
                "id": item["id"],
                "full_name": item["full_name"],
                "html_url": item["html_url"],
                "description": item["description"],
                "stargazers_count": item["stargazers_count"],
                "language": item["language"],
                "created_at": item["created_at"],
                "topics": item.get("topics", [])
            })
            if len(selected_repos) >= limit_per_cat:
                break
                
        print(f"    -> Found {len(selected_repos)} unique top repos.")
        output_data["categories"].append({
            "id": cat["id"],
            "name": cat["name"],
            "description": cat["description"],
            "repos": selected_repos
        })
        
        # Polite delay to avoid hitting rate limits when running without auth token
        if not token and idx < len(DEFAULT_CATEGORIES) - 1:
            print("    -> Waiting 4 seconds to respect GitHub API unauthenticated limits...")
            time.sleep(4)
            
    # Save JSON
    json_path = "curated_repos.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n[✓] Saved raw data to: {json_path}")
    
    # Save Markdown
    md_content = generate_markdown(output_data, author=author)
    readme_path = "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[✓] Generated awesome list: {readme_path}")
    print(f"[✓] Total repositories curated: {len(seen_repos)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Curate top GitHub repos from 2024 onwards safely.")
    parser.add_argument("--limit", type=int, default=6, help="Max repos per category (default: 6)")
    parser.add_argument("--token", type=str, default=os.getenv("GITHUB_TOKEN"), help="GitHub Personal Access Token (optional, for higher rate limits)")
    parser.add_argument("--author", type=str, default="BenSnn", help="GitHub username for badges (default: BenSnn)")
    args = parser.parse_args()
    
    run_curator(limit_per_cat=args.limit, token=args.token, author=args.author)
