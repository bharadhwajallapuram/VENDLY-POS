def answer_question(question: str) -> str:
    """
    Return an answer to a natural language analytics question.
    For demo: keyword-based answers. LLM integration ready.
    """
    q = question.lower()
    if "top seller" in q:
        return "The top seller last month was Product X."
    if "total sales" in q:
        return "Total sales last week were $12,345."
    if "inventory" in q:
        return "Current inventory is 1,234 units."
    return "This is a sample answer. (LLM integration ready)"
