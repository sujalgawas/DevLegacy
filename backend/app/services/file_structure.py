import os
import re

DEPENDENCY_FILES = {
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
    "packages.config",
    # Rust
    "Cargo.toml", "Cargo.lock",
    # Docker
    "docker-compose.yml", "docker-compose.yaml",
}


class FileStructure:
    def __init__(self, file_structure: list, initial_score: int = 100):
        self.file_structure = file_structure or []
        self.initial_score = initial_score
        self._basenames = {os.path.basename(f).lower() for f in self.file_structure}
        self._dep_files_lower = {f.lower() for f in DEPENDENCY_FILES}

    def contains_test(self) -> bool:
        for path in self.file_structure:
            if "test" in path.lower():
                return True
        return False

    def contains_gitignore(self) -> bool:
        return ".gitignore" in self._basenames

    def contains_dependency_management(self) -> bool:
        # Fast set intersection O(1) avg
        if self._basenames & self._dep_files_lower:
            return True
        # Check extensions like .csproj
        return any(path.endswith(".csproj") for path in self.file_structure)

    def env_configuration(self) -> int:
        result = 5
        for path in self.file_structure:
            lower = path.lower()
            if ".env.example" in lower or ".env.template" in lower:
                result += 5
            elif lower.endswith(".env") or "/.env" in lower or "\\.env" in lower:
                result -= 5
        return result

    def contains_readme(self) -> bool:
        return any("readme.md" in b for b in self._basenames)

    def check_depth(self) -> int:
        pattern = r"[\\/]"
        max_depth = 0
        for path in self.file_structure:
            depth = re.split(pattern, path)
            max_depth = max(max_depth, len(depth))
        return max_depth

    def score(self) -> int:
        # Calculate score without mutating self.initial_score
        current_score = self.initial_score

        if not self.contains_test():
            current_score -= 25

        if not self.contains_gitignore():
            current_score -= 15

        if not self.contains_dependency_management():
            current_score -= 15

        env_config = self.env_configuration()
        if env_config == 5:
            current_score -= 10
        elif env_config <= 0:
            current_score -= 20

        if not self.contains_readme():
            current_score -= 15

        depth = self.check_depth()
        if depth < 2:
            current_score -= 20
        elif not (3 < depth < 7):
            current_score -= 10

        return max(0, current_score)


def get_file_structure_score(final_dir: dict) -> int:
    """
    Compute the average file structure score across up to 4 pinned repos.
    Returns:
        Score out of 10 (rounded).
    """
    if not final_dir:
        return 0

    repo_names = list(final_dir.keys())[:4]
    total_score = 0
    count = 0

    for repo_name in repo_names:
        file_list = final_dir[repo_name]
        if file_list:
            fs = FileStructure(file_structure=file_list, initial_score=100)
            total_score += fs.score()
            count += 1

    if count == 0:
        return 0

    average_score = total_score / count
    return round(average_score / 10)
