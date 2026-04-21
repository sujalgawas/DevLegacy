import logging
import os 
import requests
from dotenv import load_dotenv
from firebase_admin import auth
import json
from jupyter_notebook_parser import SourceCodeContainer

load_dotenv()
github_client_id = os.getenv("github_client_id")
github_secret = os.getenv("github_secret")
github_access_token = os.getenv("github_access_token")



def _github_headers():
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if github_access_token:
        h["Authorization"] = f"token {github_access_token}"
    return h

#function to verify firebase token
def verify_token(token):
    decoded_token = auth.verify_id_token(token)
    uid = decoded_token['uid']
    return uid

#function to call github api
def github_api(query : str,variable = None):
    url = "https://api.github.com/graphql"
    
    header = {
        'Authorization': f'Bearer {github_access_token}',
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    
    json_data = {"query":query}
    if variable:
        json_data["variables"] = variable
        
    response = requests.post(url=url,json=json_data,headers=header)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"query failed {response.status_code}:{response.text}") 

logger = logging.getLogger(__name__)

def jupternotebook_cleaner(text):
    if not text:
        return ""

    try:
        notebook_json = json.loads(text)
        
        final_clean_code = []
        
        if 'cells' in notebook_json:
            for cell in notebook_json['cells']:
                if cell.get('cell_type') == 'code':
                    raw_source = "".join(cell.get('source', []))
                    container = SourceCodeContainer(raw_source)
                    
                    clean_code = container.source_without_magic
                    if clean_code.strip():
                        final_clean_code.append(clean_code)
                        
        return '\n'.join(final_clean_code)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Jupyter Notebook JSON: {str(e)}")
        logger.error(f"Snippet of invalid text: {text[-100:]}") 
        return ""

#function to get user id from username
def get_user_id(login):
    """Helper to get the Node ID for a username (required for filtering history)"""
    query = """
    query($login: String!) {
        user(login: $login) { id }
    }
    """
    data = github_api(query, {'login': login})
    return data['data']['user']['id']



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
    "Firebase": [r"\bfirebase_admin\b", r"\bfirestore\b", r"\bfirebase\b"],
    # --- Docker / Infra ---
    "Docker": [r"\bdockerfile\b", r"\bdocker-compose\b", r"\"docker\""],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b", r"\bkubectl\b"],
    # --- Flutter ---
    "Flutter": [r"\bflutter\b", r"\"dart\""],
}

MIN_MATCHES = {1: 1, 2: 2, 3: 1}

INDICATOR_FILES = [
    "package.json", "package-lock.json",
    "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "setup.cfg",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    "Gemfile", "build.gradle", "pom.xml", "go.mod", "Cargo.toml",
    "README.md", "README.txt", "readme.md",
]

ROLE_DATASET = {
    "Frontend Developer": [
        "React", "Next.js", "Angular", "Vue.js", "Svelte", "Nuxt.js", 
        "Gatsby", "jQuery", "Redux", "Three.js", "Vite", "Tailwind CSS", 
        "Bootstrap", "Sass", "Material UI", "Blazor"
    ],
    "Backend Developer": [
        "Django", "FastAPI", "Flask", "Express.js", "Spring Boot", 
        "NestJS", "Laravel", "Tornado", "Pyramid", "Hibernate", "Gin", 
        "Echo", "Fiber", "Symfony", "CodeIgniter", "ASP.NET", ".NET Core", 
        "Actix", "Rocket", "Ktor", "Celery", "SQLAlchemy", "GORM", 
        "Entity Framework", "Tokio", "Diesel", "Maven", "Gradle", "JUnit"
    ],
    "AI/ML Engineer & Data Scientist": [
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", 
        "NumPy", "Scrapy", "Streamlit", "Dash", "OpenCV", "CUDA"
    ],
    "Mobile Developer": [
        "Flutter", "Xamarin", "Jetpack Compose", "Android SDK"
    ],
    "Game & Desktop Developer": [
        "Electron", "Unity", "Qt", "Love2D", "OpenGL", "Boost", "CMake"
    ],
    "Database Engineer": [
        "PostgreSQL", "MySQL", "MongoDB", "SQLite", "Redis", 
        "Firebase", "Supabase"
    ],
    "DevOps Engineer": [
        "Docker", "Kubernetes"
    ],
    "CMS Developer": [
        "WordPress"
    ]
}

def sanitize_data(data):
    return data
