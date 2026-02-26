import re


class FileStructure:
    def __init__(self, file_structure, initial_score=100):
        self.file_structure = file_structure
        self.initial_score = initial_score
        
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
    
    def contains_dependency_management(self):
        dependency_files = [
            # Python
            "requirements.txt", "pyproject.toml", "Pipfile", "Pipfile.lock",
            "setup.py", "environment.yml",
            # JavaScript / TypeScript
            "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            # Java / Kotlin
            "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
            # C / C++
            "CMakeLists.txt", "Makefile", "conanfile.txt", "vcpkg.json",
            # Go
            "go.mod", "go.sum",
            # PHP
            "composer.json", "composer.lock",
            # C#
            "packages.config", ".csproj",
            # Rust
            "Cargo.toml", "Cargo.lock",
            # Docker
            "docker-compose.yml", "docker-compose.yaml"
        ]
        
        for dep_file in dependency_files:
            for sub_folder in self.file_structure:
                if dep_file in sub_folder:
                    return True
        return False
    
    def env_configuration(self):
        result = 5
        for sub_folder in self.file_structure:
            if ".env.example" in sub_folder or ".env.template" in sub_folder:
                result += 5
            elif sub_folder.endswith(".env") or ".env" in sub_folder:
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
            max_depth = max(max_depth, len(depth))
        return max_depth
        
    def score(self):
        if not self.contains_test():
            self.initial_score -= 25
        
        if not self.contains_gitignore():
            self.initial_score -= 15
        
        if not self.contains_dependency_management():
            self.initial_score -= 15
        
        env_config = self.env_configuration()
        if env_config == 5:
            self.initial_score -= 10
        elif env_config == 0:
            self.initial_score -= 20
        
        if not self.contains_readme():
            self.initial_score -= 15
        
        check_depth = self.check_depth()
        if check_depth < 2:
            self.initial_score -= 20
        if not 7 > check_depth > 3:
            self.initial_score -= 20
        
        return self.initial_score


def get_file_structure_score(final_dir: dict) -> int:
    """
    Compute the average file structure score across up to 4 pinned repos.
    
    Args:
        final_dir: dict mapping repo names to lists of file paths,
                   e.g. {"repo1": ["src/main.py", "README.md", ...], ...}
    
    Returns:
        Score out of 10 (rounded).
    """
    if not final_dir:
        return 0
    
    # Consider at most 4 pinned repos
    repo_names = list(final_dir.keys())[:4]
    
    total_score = 0
    count = 0
    
    for repo_name in repo_names:
        file_list = final_dir[repo_name]
        if file_list:
            fs = FileStructure(file_structure=file_list, initial_score=100)
            repo_score = fs.score()
            total_score += max(repo_score, 0)  # clamp negative scores to 0
            count += 1
    
    if count == 0:
        return 0
    
    average_score = total_score / count
    return round(average_score / 10)
