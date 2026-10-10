# File-structure scoring

The file-structure service is implemented in [`file_structure.py`](../backend/app/services/file_structure.py). It evaluates up to four repositories from the documentation/code-fetch result.

```mermaid
flowchart TD
    A[Repository file paths] --> B[FileStructure helper]
    B --> C{Tests present?}
    B --> D{.gitignore present?}
    B --> E{Dependency manifest present?}
    B --> F{Environment template safe?}
    B --> G{README present?}
    B --> H[Calculate maximum path depth]
    C --> I[Apply score penalties]
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    I --> J[Clamp score to 0-100]
    J --> K[Average repositories and divide by 10]
```

The checks reward a recognizable project layout and penalize missing tests, `.gitignore`, dependency management, README documentation, environment templates, or a useful directory depth. A committed `.env` is penalized more heavily than a missing template. The final helper returns an average score out of 10 for the selected repositories.
