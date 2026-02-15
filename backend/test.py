import requests
import json
import subprocess
import tempfile
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re

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


url = "https://api.github.com/search/repositories"
header = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

repo_url = "https://github.com/sujalgawas/DevLegacy"
framework_data = [
    # Python (.py)
    "FastAPI", "Django", "Flask", "Tornado", "Pyramid", "Celery",
    "SQLAlchemy", "Pandas", "NumPy", "TensorFlow", "PyTorch", "Keras",
    "Scikit-learn", "Scrapy", "Streamlit", "Dash",
    # JavaScript / TypeScript (.js, .ts, .tsx)
    "React", "Next.js", "Angular", "Vue.js", "Express.js", "NestJS",
    "Svelte", "Nuxt.js", "Gatsby", "jQuery", "Redux", "Three.js",
    "Electron", "Vite",
    # Java (.java)
    "Spring Boot", "Hibernate", "Maven", "Gradle", "Android SDK", "JUnit",
    # Go (.go)
    "Gin", "Echo", "Fiber", "GORM",
    # PHP (.php)
    "Laravel", "Symfony", "WordPress", "CodeIgniter",
    # C# (.cs)
    "ASP.NET", ".NET Core", "Entity Framework", "Unity", "Blazor", "Xamarin",
    # Rust (.rs)
    "Actix", "Rocket", "Tokio", "Diesel",
    # Kotlin (.kt)
    "Ktor", "Jetpack Compose",
    # C / C++ (.c, .cpp, .cc, .cxx)
    "Qt", "OpenGL", "Boost", "CMake", "OpenCV", "CUDA",
    # CSS (.css)
    "Tailwind CSS", "Bootstrap", "Sass", "Material UI",
    # Lua (.lua)
    "Love2D",
    # SQL / Databases
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Supabase", "Firebase",
    # Docker / Infra
    "Docker", "Kubernetes",
    # Flutter (Dart)
    "Flutter",
]


def get_framework(repo_url, framework_data):
    """
    Detects frameworks by cloning the repo and analyzing local files from the temp directory.
    Returns a list of detected framework names.
    """
    print(f"Scanning repository: {repo_url}...")
    
    # Clone repo and get code data from temp directory (no GitHub REST API)
    _, code = directory(repo_url)
    
    if not code:
        print("No content found or repository is private/inaccessible.")
        return []

    # Keyword patterns for each framework (case-insensitive regex with word boundaries)
    framework_keywords = {
        # --- Python ---
        "FastAPI": [r"\bfastapi\b"],
        "Django": [r"\bdjango\b"],
        "Flask": [r"\bflask\b"],
        "Tornado": [r"\btornado\b"],
        "Pyramid": [r"\bpyramid\b"],
        "Celery": [r"\bcelery\b"],
        "SQLAlchemy": [r"\bsqlalchemy\b"],
        "Pandas": [r"\bpandas\b"],
        "NumPy": [r"\bnumpy\b"],
        "TensorFlow": [r"\btensorflow\b"],
        "PyTorch": [r"\bpytorch\b", r"\btorch\b"],
        "Keras": [r"\bkeras\b"],
        "Scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
        "Scrapy": [r"\bscrapy\b"],
        "Streamlit": [r"\bstreamlit\b"],
        "Dash": [r"\bdash\b", r"\bplotly\b"],
        # --- JavaScript / TypeScript ---
        "React": [r"\breact\b", r"\breactjs\b", r"\breact-dom\b"],
        "Next.js": [r"\bnextjs\b", r"\bnext\.js\b", r"\"next\""],
        "Angular": [r"\bangular\b", r"@angular/"],
        "Vue.js": [r"\bvue\b", r"\bvuejs\b", r"\bvue\.js\b"],
        "Express.js": [r"\bexpress\b", r"\bexpressjs\b"],
        "NestJS": [r"\bnestjs\b", r"@nestjs/"],
        "Svelte": [r"\bsvelte\b"],
        "Nuxt.js": [r"\bnuxt\b", r"\bnuxtjs\b"],
        "Gatsby": [r"\bgatsby\b"],
        "jQuery": [r"\bjquery\b"],
        "Redux": [r"\bredux\b", r"\breact-redux\b"],
        "Three.js": [r"\bthree\b", r"\bthreejs\b", r"\bthree\.js\b"],
        "Electron": [r"\belectron\b"],
        "Vite": [r"\bvite\b"],
        # --- Java ---
        "Spring Boot": [r"\bspring-boot\b", r"\bspringboot\b", r"\bspring\b"],
        "Hibernate": [r"\bhibernate\b"],
        "Maven": [r"\bmaven\b", r"\bpom\.xml\b"],
        "Gradle": [r"\bgradle\b"],
        "Android SDK": [r"\bandroid\b", r"\bandroidx\b"],
        "JUnit": [r"\bjunit\b"],
        # --- Go ---
        "Gin": [r"\bgin-gonic\b", r"\bgin\b"],
        "Echo": [r"\blabstack/echo\b", r"\becho\b"],
        "Fiber": [r"\bgofiber\b", r"\bfiber\b"],
        "GORM": [r"\bgorm\b"],
        # --- PHP ---
        "Laravel": [r"\blaravel\b"],
        "Symfony": [r"\bsymfony\b"],
        "WordPress": [r"\bwordpress\b", r"\bwp-content\b"],
        "CodeIgniter": [r"\bcodeigniter\b"],
        # --- C# ---
        "ASP.NET": [r"\basp\.net\b", r"\baspnet\b"],
        ".NET Core": [r"\b\.net\b", r"\bdotnet\b", r"\bnetcoreapp\b"],
        "Entity Framework": [r"\bentityframework\b", r"\befcore\b", r"\bentity framework\b"],
        "Unity": [r"\bunityengine\b", r"\bunity\b"],
        "Blazor": [r"\bblazor\b"],
        "Xamarin": [r"\bxamarin\b"],
        # --- Rust ---
        "Actix": [r"\bactix\b", r"\bactix-web\b"],
        "Rocket": [r"\brocket\b"],
        "Tokio": [r"\btokio\b"],
        "Diesel": [r"\bdiesel\b"],
        # --- Kotlin ---
        "Ktor": [r"\bktor\b"],
        "Jetpack Compose": [r"\bjetpack compose\b", r"\bcompose\b", r"\bandroidx\.compose\b"],
        # --- C / C++ ---
        "Qt": [r"\bqt\b", r"\bqwidget\b", r"\bqapplication\b"],
        "OpenGL": [r"\bopengl\b", r"\bglfw\b", r"\bglut\b"],
        "Boost": [r"\bboost\b"],
        "CMake": [r"\bcmake\b", r"\bcmakelists\b"],
        "OpenCV": [r"\bopencv\b", r"\bcv2\b"],
        "CUDA": [r"\bcuda\b", r"\bnvcc\b"],
        # --- CSS ---
        "Tailwind CSS": [r"\btailwindcss\b", r"\btailwind\b"],
        "Bootstrap": [r"\bbootstrap\b"],
        "Sass": [r"\bsass\b", r"\bscss\b"],
        "Material UI": [r"\bmaterial-ui\b", r"\b@mui\b", r"\bmuicss\b"],
        # --- Lua ---
        "Love2D": [r"\blove2d\b", r"\blove\.graphics\b"],
        # --- Databases ---
        "PostgreSQL": [r"\bpostgres\b", r"\bpostgresql\b", r"\bpsycopg2\b"],
        "MySQL": [r"\bmysql\b", r"\bmariadb\b"],
        "SQLite": [r"\bsqlite\b", r"\bsqlite3\b"],
        "MongoDB": [r"\bmongodb\b", r"\bmongoose\b", r"\bpymongo\b"],
        "Redis": [r"\bredis\b"],
        "Supabase": [r"\bsupabase\b"],
        "Firebase": [r"\bfirebase\b", r"\bfirestore\b"],
        # --- Docker / Infra ---
        "Docker": [r"\bdocker\b", r"\bdockerfile\b"],
        "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b", r"\bkubectl\b"],
        # --- Flutter ---
        "Flutter": [r"\bflutter\b", r"\bdart\b"],
    }

    code_lower = code.lower()

    print("\nFramework Detection Results:")
    print("-" * 40)
    
    detected = []
    for framework in framework_data:
        patterns = framework_keywords.get(framework, [r"\b" + re.escape(framework.lower()) + r"\b"])
        
        total_matches = 0
        for pattern in patterns:
            matches = re.findall(pattern, code_lower)
            total_matches += len(matches)
        
        if total_matches > 0:
            print(f"{framework:<20} → {total_matches} matches ✓")
            detected.append(framework)
            
    if not detected:
        print("\nNo frameworks detected.")

    return detected

# Run the function
detected_frameworks = get_framework(repo_url, framework_data)

print(f"\nFinal detected frameworks: {detected_frameworks}")

final_string = ""
for x in detected_frameworks:
    temp_str = "topic:" + x
    if final_string:
        final_string = final_string + " OR " + temp_str
    else:
        final_string = temp_str

query = {"q": final_string,
        "sort": "stars",
        "order": "desc",
        "per_page": 1}

print(f"\n[DEBUG] Search query: {final_string}")

response = requests.get(url=url, params=query, headers=header)

if response.status_code == 200:
    try:
        data = response.json()
    except Exception as e:
        print(f"error in {e}")
        data = {"items": []}
else:
    print(f"{response.status_code}")
    data = {"items": []}

if not data.get("items"):
    print("No template repository found. Exiting.")
    exit()

top_repo = data["items"][0]
template_url = top_repo["html_url"]
print(f"Template repo found: {template_url}")


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
