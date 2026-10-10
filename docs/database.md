# Database

DevLegacy uses PostgreSQL through SQLAlchemy. Each analysis is keyed by the authenticated/user identifier (`uid`). Instead of one wide result table, the backend stores related result categories in separate tables. JSONB is used where the shape is naturally nested, such as repository counts, issues, detected frameworks, and code snapshots.

![DevLegacy database structure](../github_database.png)

```mermaid
erDiagram
    USERS ||--o{ GITHUB_PROFILE : owns
    USERS ||--o{ CODE : stores
    USERS ||--o{ CODE_QUALITY : receives
    USERS ||--o{ COMMIT_STATUS : records
    USERS ||--o{ CONSISTENCY_STATUS : records
    USERS ||--o{ DOCUMENT_STATS : records
    USERS ||--o{ OPEN_SOURCE : records
    USERS ||--o{ TECH_STACK : records

    USERS {
        string uid PK
        string email
        string username
    }
    GITHUB_PROFILE {
        string uid PK
        string name
        int public_repo
        int followers
        int following
        int final_score
        jsonb recommended_role
        jsonb detected_frameworks
    }
    CODE {
        string uid PK
        jsonb code
    }
    CODE_QUALITY {
        string uid PK
        int code_score
        string code_level
    }
    COMMIT_STATUS {
        string uid PK
        int total_commits
        jsonb commits_per_repo
    }
    CONSISTENCY_STATUS {
        string uid PK
        int total_contributions
        int longest_streak
        int current_streak
        int active_days
    }
    DOCUMENT_STATS {
        string uid PK
        int avg_lines_readme
        int comment_percentage
        jsonb comment_to_repos
        jsonb final_dir
    }
    OPEN_SOURCE {
        string uid PK
        jsonb pull_requests
        jsonb issues
        string[] repositories_contributed_to
        jsonb code_reviews
    }
    TECH_STACK {
        string uid PK
        string[] all_languages
        jsonb language_with_code_byte
    }
```

The image is the visual reference for the project schema. The Mermaid diagram documents the logical relationship: the tables are related by `uid`, even though the current model files primarily express those keys as independent primary-key columns rather than SQLAlchemy relationship declarations.
