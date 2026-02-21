import requests
import json
import subprocess
import tempfile
import os
import time
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re
from dotenv import load_dotenv

load_dotenv()
# --- GitHub Authentication ---
# Set your GitHub token as an environment variable: GITHUB_TOKEN=ghp_xxxxx
GITHUB_TOKEN = os.getenv("github_access_token", "")


def clean_paths(paths, max_depth=3):
    cleaned = set()
    for path in paths:
        path = path.replace("\\", "/").lower()
        path = os.path.splitext(path)[0]
        path = path.strip("/")
        parts = path.split("/")
        cleaned.add("/".join(parts))
        
    return sorted(cleaned)


def directory(url):
    """
    Clones a GitHub repo into a temp directory, extracts:
    - ideal_structure: file paths via cloc
    - code_data: text corpus built from file paths + README (for framework detection)
    """
    ideal_structure = []
    code_data = ""

    with tempfile.TemporaryDirectory() as tempdirname:
        clone_result = subprocess.run(args=["git", "clone", url, tempdirname], capture_output=True, text=True)
        print(f"[DEBUG] Clone return code: {clone_result.returncode}")
        if clone_result.returncode != 0:
            print(f"[DEBUG] Clone stderr: {clone_result.stderr}")

        # --- Get file structure via cloc ---
        result = subprocess.run(args=["cloc", "--by-file", "--json", tempdirname],
                                capture_output=True,
                                text=True,
                                check=True)
        
        data = json.loads(result.stdout)
        json_head = data.keys()

        for dict_key in json_head:
            if tempdirname in dict_key:
                length = len(tempdirname)
                final_output = dict_key[length:]
                ideal_structure.append(final_output)

        # --- Build text corpus from the cloned files (replaces GitHub REST API) ---
        # 1. Gather all file paths by walking the cloned directory
        file_paths = []
        for root, dirs, files in os.walk(tempdirname):
            # Skip .git directory
            dirs[:] = [d for d in dirs if d != '.git']
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, tempdirname)
                file_paths.append(relative_path.replace("\\", "/"))

        code_data = " ".join(file_paths)
        print(f"[DEBUG] Total file paths found: {len(file_paths)}")

        # 2. Read dependency/config files where framework names are explicitly mentioned
        indicator_files = [
            "package.json", "package-lock.json",
            "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "setup.cfg",
            "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
            "Gemfile", "build.gradle", "pom.xml", "go.mod", "Cargo.toml",
            "README.md", "README.txt", "readme.md",
        ]
        
        for root, dirs, files in os.walk(tempdirname):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
            for file in files:
                if file in indicator_files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            code_data += " " + content
                            print(f"[DEBUG] Read indicator file: {os.path.relpath(file_path, tempdirname)} ({len(content)} chars)")
                    except:
                        pass

    print(f"[DEBUG] Total code_data length: {len(code_data)} chars")
    return ideal_structure, code_data


# --- GitHub API Config (authenticated = 5000 req/hr, no delays needed) ---
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

def _github_headers():
    """Build GitHub API headers, with token auth if available."""
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h


repo_url = "https://github.com/mesa/mesa"

# =============================================================================
# FRAMEWORK TIER CLASSIFICATION
# =============================================================================
# Tier 1 — PRIMARY frameworks (defines the project's core architecture)
# Tier 2 — LIBRARIES / TOOLS / CSS (subsidiary, filtered from output)
# Tier 3 — INFRASTRUCTURE / DATABASES (reported in output)

FRAMEWORK_TIERS = {
    # --- Tier 1: Primary Frameworks ---
    "FastAPI": 1, "Django": 1, "Flask": 1, "Tornado": 1, "Pyramid": 1,
    "TensorFlow": 1, "PyTorch": 1, "Keras": 1, "Scikit-learn": 1,
    "Scrapy": 1, "Streamlit": 1, "Dash": 1,
    "React": 1, "Next.js": 1, "Angular": 1, "Vue.js": 1,
    "Express.js": 1, "NestJS": 1, "Svelte": 1, "Nuxt.js": 1, "Gatsby": 1,
    "Electron": 1,
    "Spring Boot": 1, "Hibernate": 1,
    "Gin": 1, "Echo": 1, "Fiber": 1,
    "Laravel": 1, "Symfony": 1, "WordPress": 1, "CodeIgniter": 1,
    "ASP.NET": 1, ".NET Core": 1, "Unity": 1, "Blazor": 1, "Xamarin": 1,
    "Actix": 1, "Rocket": 1,
    "Ktor": 1, "Jetpack Compose": 1,
    "Qt": 1, "Love2D": 1,
    "Flutter": 1,

    # --- Tier 2: Libraries / Tools / CSS (filtered out) ---
    "Celery": 2, "SQLAlchemy": 2, "Pandas": 2, "NumPy": 2,
    "jQuery": 2, "Redux": 2, "Three.js": 2, "Vite": 2,
    "Maven": 2, "Gradle": 2, "Android SDK": 2, "JUnit": 2,
    "GORM": 2, "Entity Framework": 2, "Tokio": 2, "Diesel": 2,
    "OpenGL": 2, "Boost": 2, "CMake": 2, "OpenCV": 2, "CUDA": 2,
    "Tailwind CSS": 2, "Bootstrap": 2, "Sass": 2, "Material UI": 2,

    # --- Tier 3: Infrastructure / Databases ---
    "PostgreSQL": 3, "MySQL": 3, "SQLite": 3, "MongoDB": 3,
    "Redis": 3, "Supabase": 3, "Firebase": 3,
    "Docker": 3, "Kubernetes": 3,
}

# All frameworks we scan for (keys from the tiers dict)
framework_data = list(FRAMEWORK_TIERS.keys())

# Popularity score (higher = more important, dropped last)
FRAMEWORK_POPULARITY = {
    # Tier 1
    "React": 100, "Next.js": 95, "Django": 95, "Angular": 90,
    "Vue.js": 90, "FastAPI": 85, "Flask": 85, "Express.js": 85,
    "Spring Boot": 85, "NestJS": 80, "Svelte": 78, "Nuxt.js": 75,
    "Flutter": 80, "Laravel": 80, "Gatsby": 65, "Electron": 60,
    "TensorFlow": 75, "PyTorch": 75, "Keras": 65, "Scikit-learn": 65,
    "Scrapy": 55, "Streamlit": 60, "Dash": 55,
    "Tornado": 50, "Pyramid": 45,
    "Hibernate": 60, "Gin": 60, "Echo": 55, "Fiber": 50,
    "Symfony": 60, "WordPress": 70, "CodeIgniter": 45,
    "ASP.NET": 65, ".NET Core": 70, "Unity": 60, "Blazor": 50, "Xamarin": 45,
    "Actix": 45, "Rocket": 40, "Ktor": 45, "Jetpack Compose": 55,
    "Qt": 50, "Love2D": 25,
    # Tier 2 (won't be in the search, but just in case)
    "Celery": 40, "SQLAlchemy": 45, "Pandas": 55, "NumPy": 55,
    "jQuery": 50, "Redux": 55, "Three.js": 45, "Vite": 50,
    "Maven": 40, "Gradle": 40, "Android SDK": 40, "JUnit": 35,
    "GORM": 35, "Entity Framework": 40, "Tokio": 40, "Diesel": 30,
    "OpenGL": 40, "Boost": 35, "CMake": 35, "OpenCV": 45, "CUDA": 40,
    "Tailwind CSS": 55, "Bootstrap": 50, "Sass": 40, "Material UI": 50,
    # Tier 3
    "PostgreSQL": 70, "MySQL": 65, "MongoDB": 65, "SQLite": 50,
    "Redis": 55, "Firebase": 55, "Supabase": 50,
    "Docker": 50, "Kubernetes": 45,
}


# =============================================================================
# FRAMEWORK DETECTION (tightened regex patterns)
# =============================================================================

# Keyword patterns — tightened to avoid false positives from ambiguous terms
FRAMEWORK_KEYWORDS = {
    # --- Python ---
    "FastAPI": [r"\bfastapi\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "Tornado": [r"\btornado\.web\b", r"\btornado\.ioloop\b", r"\"tornado\""],
    "Pyramid": [r"\bpyramid\b"],
    "Celery": [r"\bcelery\b"],
    "SQLAlchemy": [r"\bsqlalchemy\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "PyTorch": [r"\bpytorch\b", r"\bimport torch\b", r"\"torch\""],
    "Keras": [r"\bkeras\b"],
    "Scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
    "Scrapy": [r"\bscrapy\b"],
    "Streamlit": [r"\bstreamlit\b"],
    "Dash": [r"\bdash\b", r"\bplotly\b"],
    # --- JavaScript / TypeScript ---
    "React": [r"\"react\"", r"\breact-dom\b", r"from ['\"]react['\"]", r"\breactjs\b"],
    "Next.js": [r"\"next\"", r"\bnext\.js\b", r"\bnextjs\b", r"next\.config"],
    "Angular": [r"@angular/", r"\bangular\.json\b"],
    "Vue.js": [r"\"vue\"", r"\bvuejs\b", r"\bvue\.config\b"],
    "Express.js": [r"\"express\"", r"require\(['\"]express['\"]\)", r"from ['\"]express['\"]"],
    "NestJS": [r"@nestjs/", r"\bnestjs\b"],
    "Svelte": [r"\bsvelte\b"],
    "Nuxt.js": [r"\bnuxt\b", r"\bnuxtjs\b"],
    "Gatsby": [r"\bgatsby\b"],
    "jQuery": [r"\bjquery\b"],
    "Redux": [r"\bredux\b", r"\breact-redux\b"],
    "Three.js": [r"\"three\"", r"\bthreejs\b"],
    "Electron": [r"\"electron\"", r"require\(['\"]electron['\"]\)"],
    "Vite": [r"\"vite\"", r"\bvite\.config\b"],
    # --- Java ---
    "Spring Boot": [r"\bspring-boot\b", r"\bspringboot\b", r"org\.springframework\b"],
    "Hibernate": [r"\bhibernate\b"],
    "Maven": [r"\bpom\.xml\b", r"\bmaven\b"],
    "Gradle": [r"\bbuild\.gradle\b", r"\bgradle\b"],
    "Android SDK": [r"\bandroidx\b", r"\bandroid-sdk\b", r"com\.android\b"],
    "JUnit": [r"\bjunit\b", r"org\.junit\b"],
    # --- Go ---
    "Gin": [r"\bgin-gonic\b", r"\"github\.com/gin-gonic/gin\""],
    "Echo": [r"\blabstack/echo\b"],
    "Fiber": [r"\bgofiber\b", r"\"github\.com/gofiber/fiber\""],
    "GORM": [r"\bgorm\.io\b", r"\"gorm\""],
    # --- PHP ---
    "Laravel": [r"\blaravel\b"],
    "Symfony": [r"\bsymfony\b"],
    "WordPress": [r"\bwordpress\b", r"\bwp-content\b"],
    "CodeIgniter": [r"\bcodeigniter\b"],
    # --- C# ---
    "ASP.NET": [r"\basp\.net\b", r"\baspnet\b"],
    ".NET Core": [r"\bdotnet\b", r"\bnetcoreapp\b", r"Microsoft\.NET\.Sdk"],
    "Entity Framework": [r"\bentityframework\b", r"\befcore\b"],
    "Unity": [r"\bunityengine\b", r"UnityEditor\b"],
    "Blazor": [r"\bblazor\b"],
    "Xamarin": [r"\bxamarin\b"],
    # --- Rust ---
    "Actix": [r"\bactix\b", r"\bactix-web\b"],
    "Rocket": [r"\"rocket\"", r"\brocket::"],
    "Tokio": [r"\btokio\b"],
    "Diesel": [r"\"diesel\"", r"\bdiesel::\b"],
    # --- Kotlin ---
    "Ktor": [r"\bktor\b"],
    "Jetpack Compose": [r"\bjetpack compose\b", r"\bandroidx\.compose\b"],
    # --- C / C++ ---
    "Qt": [r"\bQWidget\b", r"\bQApplication\b", r"\bQT\b", r"#include <Q"],
    "OpenGL": [r"\bopengl\b", r"\bglfw\b", r"\bglut\b"],
    "Boost": [r"\bboost::\b", r"\"boost\""],
    "CMake": [r"\bCMakeLists\.txt\b", r"\bcmake\b"],
    "OpenCV": [r"\bopencv\b", r"\bcv2\b"],
    "CUDA": [r"\bcuda\b", r"\bnvcc\b"],
    # --- CSS ---
    "Tailwind CSS": [r"\"tailwindcss\"", r"tailwind\.config"],
    "Bootstrap": [r"\"bootstrap\"", r"bootstrap\.min"],
    "Sass": [r"\"sass\"", r"\"node-sass\""],
    "Material UI": [r"\"@mui/", r"\"material-ui\""],
    # --- Lua ---
    "Love2D": [r"\blove2d\b", r"\blove\.graphics\b"],
    # --- Databases ---
    "PostgreSQL": [r"\bpostgres\b", r"\bpostgresql\b", r"\bpsycopg2\b", r"\bpg\b"],
    "MySQL": [r"\bmysql\b", r"\bmariadb\b"],
    "SQLite": [r"\bsqlite\b", r"\bsqlite3\b"],
    "MongoDB": [r"\bmongodb\b", r"\bmongoose\b", r"\bpymongo\b"],
    "Redis": [r"\bredis\b"],
    "Supabase": [r"\bsupabase\b"],
    "Firebase": [r"\bfirebase_admine\b", r"\bfirestore\b"],
    # --- Docker / Infra ---
    "Docker": [r"\bdockerfile\b", r"\bdocker-compose\b", r"\"docker\""],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b", r"\bkubectl\b"],
    # --- Flutter ---
    "Flutter": [r"\bflutter\b", r"\"dart\""],
}

# Minimum match count required per tier to consider a framework "detected"
MIN_MATCHES = {1: 1, 2: 2, 3: 1}


def get_framework(repo_url, framework_data):
    """
    Detects frameworks by cloning the repo and analyzing local files.
    Only returns Tier 1 (primary) and Tier 3 (infrastructure) frameworks.
    Tier 2 (libraries/tools/CSS) are filtered out.
    """
    print(f"Scanning repository: {repo_url}...")

    _, code = directory(repo_url)

    if not code:
        print("No content found or repository is private/inaccessible.")
        return []

    code_lower = code.lower()

    print("\nFramework Detection Results:")
    print("-" * 50)

    detected = []
    all_matches = {}  # for debug logging

    for framework in framework_data:
        tier = FRAMEWORK_TIERS.get(framework, 2)
        patterns = FRAMEWORK_KEYWORDS.get(framework, [r"\b" + re.escape(framework.lower()) + r"\b"])

        total_matches = 0
        for pattern in patterns:
            matches = re.findall(pattern, code_lower)
            total_matches += len(matches)

        if total_matches > 0:
            all_matches[framework] = total_matches

        threshold = MIN_MATCHES.get(tier, 1)

        if total_matches >= threshold and tier in (1, 3):
            print(f"  ✓ {framework:<20} │ tier {tier} │ {total_matches} matches")
            detected.append(framework)
        elif total_matches > 0 and tier == 2:
            print(f"  ✗ {framework:<20} │ tier {tier} │ {total_matches} matches (filtered — library/tool)")
        elif total_matches > 0 and total_matches < threshold:
            print(f"  ✗ {framework:<20} │ tier {tier} │ {total_matches} matches (below threshold {threshold})")

    if not detected:
        print("\nNo primary frameworks detected.")

    return detected


# =============================================================================
# PRIORITY-BASED PROGRESSIVE GITHUB SEARCH (authenticated, no delays)
# =============================================================================

def search_github(frameworks, max_retries=10):
    """
    Search GitHub for repos matching the detected frameworks using topic: queries.
    If no results, progressively drop the least popular framework and retry.
    Uses authenticated requests (GITHUB_TOKEN) — no rate-limit delays.
    """
    headers = _github_headers()

    if not GITHUB_TOKEN:
        print("\n⚠  WARNING: No GITHUB_TOKEN set. Using unauthenticated requests (10 req/min limit).")
        print("   Set GITHUB_TOKEN env var for 5000 req/hr.\n")

    remaining = sorted(frameworks, key=lambda f: FRAMEWORK_POPULARITY.get(f, 0), reverse=True)

    attempt = 0
    while remaining and attempt < max_retries:
        attempt += 1

        query_str = " ".join(f"topic:{fw}" for fw in remaining)
        params = {
            "q": query_str,
            "sort": "stars",
            "order": "desc",
            "per_page": 1,
        }

        print(f"\n[Search attempt {attempt}] Frameworks ({len(remaining)}): {remaining}")
        print(f"  Query: {query_str}")

        response = requests.get(url=GITHUB_SEARCH_URL, params=params, headers=headers)

        if response.status_code != 200:
            print(f"  ✗ GitHub API error: {response.status_code}")
            # If rate limited and unauthenticated, wait a bit
            if response.status_code == 403 and not GITHUB_TOKEN:
                print("  Rate limited. Waiting 10s...")
                time.sleep(10)
            continue

        data = response.json()
        total_count = data.get("total_count", 0)
        items = data.get("items", [])

        print(f"  → {total_count} total results")

        if items:
            top_repo = items[0]
            print(f"  ✓ Found: {top_repo['full_name']} (⭐ {top_repo['stargazers_count']})")
            return data, remaining

        # No results — drop the least popular framework
        dropped = remaining[-1]
        print(f"  ✗ No results. Dropping least popular: {dropped} (popularity={FRAMEWORK_POPULARITY.get(dropped, 0)})")
        remaining = remaining[:-1]

    print("\n✗ No template repository found after all attempts.")
    return {"items": []}, []


# =============================================================================
# MAIN EXECUTION
# =============================================================================

# 1. Detect frameworks
detected_frameworks = get_framework(repo_url, framework_data)
print(f"\nFinal detected frameworks: {detected_frameworks}")

# 2. Search GitHub with progressive priority-based dropping
data, used_frameworks = search_github(detected_frameworks)

if not data.get("items"):
    print("No template repository found. Exiting.")
    exit()

top_repo = data["items"][0]
template_url = top_repo["html_url"]
print(f"\nTemplate repo found: {template_url}")
print(f"Frameworks used in search: {used_frameworks}")

# 3. Compare directory structures
user_dir, _ = directory(repo_url)
template_dir, _ = directory(template_url)

transformer = TfidfVectorizer()

def dir_score(user_url, template_dir, transformer):
    sorted_user = sorted(clean_paths(user_url))
    sorted_template = sorted(clean_paths(template_dir))
    print(sorted_user)
    print(sorted_template)

    user_final = "\n".join(sorted_user)
    template_final = "\n".join(sorted_template)

    user_encode = transformer.fit_transform([user_final])
    template_encode = transformer.transform([template_final])

    score = cosine_similarity(user_encode, template_encode)

    print(f"{score[0][0]:.4f}")


dir_score(user_url=user_dir, template_dir=template_dir, transformer=transformer)
