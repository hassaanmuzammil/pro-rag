def extract_json_str(text):
    """
    Extracts a JSON string from the given text.
    Args:
        text (str): The input text containing a JSON string.
    Returns:
        str: The extracted JSON string, or None if no valid JSON is found.
    """
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        json_str = text[start:end]
        return json_str
    except ValueError:
        return None
