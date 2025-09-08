import re
from collections import Counter
from typing import List


class NounExtractor:
    
    def __init__(self):
        # Common stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'this', 'that', 'these', 'those', 'is', 
            'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must'
        }
        
        # Common verb endings to exclude
        self.verb_endings = {'ing', 'ed', 'er', 'ly'}
        
        # Articles that often precede nouns
        self.articles = {'the', 'a', 'an'}

    def extract_keywords(self, text: str, top_k: int = 3) -> List[str]:
        """
        Extract nouns using pattern matching.
        
        Rules:
        1. Capitalized words (proper nouns)
        2. Words after articles (the/a/an + noun)  
        3. Words that don't look like verbs/adjectives
        4. Filter by frequency
        """
        likely_nouns = []
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            words = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
            original_words = re.findall(r'\b[a-zA-Z]+\b', sentence)  # Keep original case
            
            for i, (word, original) in enumerate(zip(words, original_words)):
                if len(word) < 3 or word in self.stop_words:
                    continue
                
                #  Capitalized words (proper nouns)
                if original[0].isupper() and i > 0:  # Skip first word of sentence
                    likely_nouns.append(word)
                    continue
                
                #   Words after articles
                if i > 0 and words[i-1] in self.articles:
                    likely_nouns.append(word)
                    continue
                
                #   Words that don't look like verbs
                if not self._looks_like_verb_or_adjective(word):
                    likely_nouns.append(word)
        
        if not likely_nouns:
            all_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            filtered_words = [w for w in all_words if w not in self.stop_words]
            word_counts = Counter(filtered_words)
        else:
            word_counts = Counter(likely_nouns)
        
        return [word for word, _ in word_counts.most_common(top_k)]
    
    def _looks_like_verb_or_adjective(self, word: str) -> bool:
        """
        heuristic to identify likely verbs/adjectives to exclude.
        """
        # Common verb endings
        if any(word.endswith(ending) for ending in self.verb_endings):
            return True
        
        # Common adjective endings  
        adj_endings = {'ful', 'less', 'ous', 'ive', 'able', 'ible', 'al'}
        if any(word.endswith(ending) for ending in adj_endings):
            return True
            
        return False

