from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

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

role_name = list(ROLE_DATASET.keys())

role_document = [" ".join(frameworks) for frameworks in ROLE_DATASET.values()]

vectorizer = CountVectorizer(lowercase=True)
role_matrix = vectorizer.fit_transform(role_document)

def get_top_roles(user_frameworks, top_n = 3):
    user_document = [" ".join(user_frameworks)]
    
    user_vector = vectorizer.transform(user_document)
    
    similarity_scores = cosine_similarity(user_vector,role_matrix)[0]
    
    top_indices = np.argsort(similarity_scores)[::-1][:top_n]
    
    results = []
    
    for idx in top_indices:
        score = similarity_scores[idx]
        if score > 0:
            results.append((role_name[idx], round(score * 100, 2)))
    
    return results

github_extracted_frameworks = ["FastAPI", "Pandas", "Docker", "PostgreSQL", "Scikit-learn"]

top_matches = get_top_roles(github_extracted_frameworks)

print("Recommended Roles:")
for role, score in top_matches:
    print(f"- {role}: {score}% match")
