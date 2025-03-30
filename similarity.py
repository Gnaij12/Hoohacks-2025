import spacy

nlp = spacy.load("en_core_web_lg") 

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity score between two text strings."""
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return doc1.similarity(doc2)

# Example usage
text1 = "I like salty fries and hamburgers."
text2 = "Fast food tastes very good."

similarity_score = calculate_similarity(text1, text2)
print(f"Similarity Score: {similarity_score:.4f}")
