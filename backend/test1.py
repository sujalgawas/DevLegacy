
from app.services.cloc import get_comment_to_code
import re


url = "https://github.com/sujalgawas/DevLegacy"

sum, file = get_comment_to_code(url)


class File_structure:
    def __init__(self,file_structure,inital_score = 100):
        self.file_structure = file_structure
        self.inital_score = inital_score
        
    def contains_test(self):
        for sub_folder in self.file_structure:
            if "test" in sub_folder:
                return True
        return False
    
    def contains_gitignore(self):
        for sub_folder in self.file_structure:
            if ".gitignore" in sub_folder:
                return True
        return False
    
    def contains_dependency_mangement(self):
        dependency_files = [
            # Python (.py)
            "requirements.txt", 
            "pyproject.toml", 
            "Pipfile", 
            "Pipfile.lock", 
            "setup.py", 
            "environment.yml",
            
            # JavaScript / TypeScript (.js, .ts, .tsx, .html, .css)
            "package.json", 
            "package-lock.json", 
            "yarn.lock", 
            "pnpm-lock.yaml",
            
            # Java / Kotlin (.java, .kt)
            "pom.xml", 
            "build.gradle", 
            "build.gradle.kts", 
            "settings.gradle",
            
            # C / C++ (.c, .cpp, .cc, .cxx)
            "CMakeLists.txt", 
            "Makefile", 
            "conanfile.txt", 
            "vcpkg.json",
            
            # Go (.go)
            "go.mod", 
            "go.sum",
            
            # PHP (.php)
            "composer.json", 
            "composer.lock",
            
            # C# (.cs)
            "packages.config", 
            ".csproj",
            
            # Rust (.rs)
            "Cargo.toml", 
            "Cargo.lock",
            
            # Docker (Dockerfile, .dockerfile)
            "docker-compose.yml",
            "docker-compose.yaml"
        ]
        
        for dependencies in dependency_files:
            for sub_folder in self.file_structure:
                if dependencies in sub_folder:
                    return True
        
        return False
    
    def env_configuration(self):
        result = 5
        for sub_folder in self.file_structure:
            if ".env.example" in sub_folder or ".env.template" in sub_folder:
                result += 5
            elif sub_folder.endswith(".env") or".env" in sub_folder:
                result -= 5
                
        return result
    
    def contains_readme(self):
        for sub_folder in self.file_structure:
            if "readme.md" in sub_folder.lower():
                return True
            
        return False
    
    def check_depth(self):
        pattern = r"[\\/]"
        max_depth = 0
        for sub_folder in self.file_structure:
            depth = re.split(pattern, sub_folder)
            max_depth = max(max_depth,len(depth))
        
        return max_depth
        
    def score(self):
        if not self.contains_test():
            self.inital_score -= 25
        
        if not self.contains_gitignore():
            self.inital_score -= 15
        
        if not self.contains_dependency_mangement():
            self.inital_score -= 15
        
        env_configuration = self.env_configuration()
        if env_configuration == 5:
            self.inital_score -= 10
        elif env_configuration == 0:
            self.inital_score -= 20
        
        if not self.contains_readme():
            self.inital_score -= 15
        
        
        check_depth = self.check_depth() 
        if check_depth < 2:
            self.inital_score -= 20
        if not 7 > check_depth > 3:
            self.inital_score -= 20
        
        return self.inital_score
        
        
file_score = File_structure(file_structure=file,inital_score=100)
print(file)
print(file_score.score())


        
        