import sys
import os
sys.path.append("/home/sujal/sujal/DevLegacy/backend")

from dotenv import load_dotenv
load_dotenv("/home/sujal/sujal/DevLegacy/backend/.env")

from app.services.helper_function import github_api, jupternotebook_cleaner

#testing this for a specific error
gitname = "Daksh256"
variables = {"owner": gitname}

def build_nested_query(depth):
    query_part = """
      object {
        ... on Blob { text }
      }
    """
    
    for _ in range(depth):
        query_part = f"""
        object {{
          ... on Blob {{ text }}
          ... on Tree {{
            entries {{
              name
              type
              {query_part}
            }}
          }}
        }}
        """
    return query_part

nested_structure = build_nested_query(8)

query = f"""
query($owner: String!) {{
    user(login: $owner) {{
        pinnedItems(first: 5, types: REPOSITORY) {{
            edges {{
                node {{
                    ... on Repository {{
                        name
                        object(expression: "HEAD:") {{
                            ... on Tree {{
                                entries {{
                                    name
                                    type
                                    {nested_structure}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
"""

result = github_api(query, variables)
repos = result.get("data", {}).get("user", {}).get("pinnedItems", {}).get("edges", [])

print("Repos retrieved:", [r.get("node", {}).get("name") for r in repos])

valid_extensions = (
    ".py", ".js", ".java", ".c", ".cpp", ".cc", ".cxx", ".go", 
    ".ts", ".tsx", ".php", ".cs", ".rs", ".sql", "Dockerfile", 
    ".dockerfile", ".kt", ".html", ".css", ".lua"
)

def extract_files_from_entries(entries_list):
    found_code = []
    for entry in entries_list:
        file_name = entry.get("name", "")
        file_type = entry.get("type", "")
                    
        if file_type == "blob":
            if file_name.endswith(valid_extensions):
                text = entry.get("object", {}).get("text", "")
                if text:
                    found_code.append(text)
            elif file_name.endswith(".ipynb"):
                text = entry.get("object",{}).get("text","")
                if text:
                    processed_text = jupternotebook_cleaner(text)
                    found_code.append(processed_text)
                
        elif file_type == "tree":
            sub_entries = entry.get("object", {}).get("entries", [])
            if sub_entries:
                found_code.extend(extract_files_from_entries(sub_entries))
                
    return found_code

code_data = {}
for repo in repos:
    repo_node = repo.get("node", {})
    repo_name = repo_node.get("name")

    root_entries = repo_node.get("object", {}).get("entries", [])
    repo_files = extract_files_from_entries(root_entries)
    if repo_files:
        code_data[repo_name] = repo_files

print("Repos in code_data:", list(code_data.keys()))
for r, f in code_data.items():
    print(f"Repo '{r}' has {len(f)} files.")