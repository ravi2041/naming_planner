def find_similar_names(new_name, existing_names):
    """
    Checks if a new campaign name already exists in the database.
    All comparisons are case-insensitive but normalized to uppercase,
    since naming rules enforce uppercase globally.

    Args:
        new_name (str): The name being added or generated.
        existing_names (list): List of existing names from the DB.

    Returns:
        list: Exact duplicate matches (if any).
    """
    if not existing_names:
        return []

    # Normalize both new name and existing ones to uppercase
    new_upper = new_name.strip().upper()
    matches = [name for name in existing_names if name.strip().upper() == new_upper]

    return matches
