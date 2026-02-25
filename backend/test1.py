
from app.services.cloc import get_comment_to_code


url = "https://github.com/sujalgawas/DevLegacy"

sum, file = get_comment_to_code(url)

class Rule:
    name : str
    score : int
    condition : function

class File_structure:
    def __init__(self,file_structure,rules,inital_score = 100):
        self.file_structure = file_structure
        self.inital_score = inital_score
        self.rules = rules
    
    def score(self):
        for rule in self.rules:
            if rule.function(self.file_structure):
                self.inital_score += rule.score
        return self.score
    
rules = [
    Rule(
        name:"contains test folder",
        score: -10,
        condition: 
    )
]
        