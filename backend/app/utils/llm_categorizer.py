"""
Local-LLM fallback for transactions the keyword scorer couldn't place.

Stage 3 of the categorization cascade (learned keywords -> bank CSV Category ->
LLM -> "Other"). Talks to an Ollama-compatible endpoint on the user's own
machine, so descriptions never leave the device. Entirely optional: when it's
disabled, unreachable or unsure, it returns None and the caller falls through to
"Other" exactly as before.

Uses urllib from the standard library rather than requests - it's one JSON POST,
and a local-first app is nicer to install with fewer dependencies.
"""
import json
import re
import urllib.request
from typing import Dict, List, Optional

from .. import config

# Shape check on a model-invented name. Kept deliberately shallow: the real
# safeguard is that new names are only suggestions the user approves in the
# upload preview before anything is written to the database.
VALID_NEW_CATEGORY = re.compile(r"^[A-Za-z][A-Za-z&' -]{0,29}$")
MAX_NEW_CATEGORY_WORDS = 3

# Cache sentinel. Once a call fails, the rest of the import skips the LLM instead
# of paying the same timeout per merchant - a down server would otherwise turn a
# large statement into minutes of waiting for nothing.
UNAVAILABLE = "__llm_unavailable__"


def llm_available(cache: Optional[Dict[str, Optional[str]]] = None) -> bool:
    """
    Whether there is a working LLM to call right now.

    Callers use this to decide whether the seeded default keywords should get a
    turn: they're the offline substitute for this stage, so they only run when
    the answer here is False. Accounts for both "never configured" and "already
    failed once during this import".
    """
    if not config.llm_is_configured():
        return False
    return not (cache is not None and UNAVAILABLE in cache)


def build_prompt(description: str, amount: float, category_names: List[str]) -> str:
    """Build the single-transaction classification prompt."""
    category_list = "\n".join(f"- {name}" for name in category_names)

    return f"""You categorize personal spending. The transaction below is an expense.

Existing categories:
{category_list}

Transaction description: "{description}"
Amount: ${abs(amount):.2f}

Rules:
1. Prefer an existing category from the list above whenever the fit is plausible. Reuse beats invention.
2. If you recognize the merchant or the kind of spending but no existing category fits,
   propose ONE new category: Title Case, at most {MAX_NEW_CATEGORY_WORDS} words, describing a
   general kind of spending - never a specific merchant (propose "Pet Care", never "Petco").
3. Answer "Other" ONLY when the description is too cryptic to identify at all, such as
   "CHECKCARD XXXX" or "POS DEBIT 4471". A recognizable merchant is never "Other".

Respond with JSON only: {{"category": "<category name>"}}"""


def _clean_answer(category: str, category_names: List[str]) -> Optional[str]:
    """
    Normalize the model's answer to a usable category name, or None.

    Existing categories match case-insensitively, since models routinely answer
    "food & dining" for a category stored as "Food & Dining".
    """
    if not category:
        return None

    # "Other" is our fallback, not an answer - treat it as an abstention so the
    # caller's own Other-handling stays the single source of truth.
    if category.lower() == "other":
        return None

    for existing in category_names:
        if existing.lower() == category.lower():
            return existing

    # The model invented something; vet its shape before offering it to the user.
    normalized = " ".join(category.split())
    if len(normalized.split()) > MAX_NEW_CATEGORY_WORDS:
        return None
    if not VALID_NEW_CATEGORY.match(normalized):
        return None

    return normalized.title()


def categorize_with_llm(
    description: str,
    amount: float,
    category_names: List[str],
    keywords: Optional[List[str]] = None,
    cache: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[str]:
    """
    Ask the local model to name a category for one transaction.

    Args:
        description: Raw transaction description from the CSV
        amount: Transaction amount (negative; only the magnitude is shown to the model)
        category_names: Current categories, offered to the model as its first choice
        keywords: Already-extracted keywords, used to key the per-import cache so
            "NORTHWIND #123" and "NORTHWIND #456" cost one call between them
        cache: Optional per-import dict; pass the same one for every row of a file

    Returns:
        A category name - either one of category_names, or a new one the model
        proposed - or None when the stage is off, unreachable, or unsure.
        Never raises: the caller's "Other" fallback must always stay reachable.
    """
    if not config.llm_is_configured():
        return None

    if cache is not None and UNAVAILABLE in cache:
        return None

    key = " ".join(sorted(keywords)) if keywords else description.strip().lower()
    if cache is not None and key in cache:
        return cache[key]

    payload = {
        "model": config.LLM_MODEL,
        "prompt": build_prompt(description, amount, category_names),
        "stream": False,
        # Ollama constrains sampling so the output is always valid JSON.
        "format": "json",
        "options": {
            # Categorization should be reproducible, not creative.
            "temperature": 0,
            # The answer is one short JSON object; don't let it ramble.
            "num_predict": 60,
        },
    }

    try:
        request = urllib.request.Request(
            f"{config.LLM_BASE_URL}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=config.LLM_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))

        answer = json.loads(body.get("response") or "{}")
        result = _clean_answer(str(answer.get("category", "")).strip(), category_names)
    except Exception as exc:
        # Any failure (server down, bad model name, malformed reply) must not
        # break an import - the row just falls through to "Other". Give up on the
        # LLM for the rest of this file rather than retrying it merchant by merchant.
        print(f"[llm] categorization unavailable ({exc}); falling back to 'Other' for this import")
        if cache is not None:
            cache[UNAVAILABLE] = None
        return None

    if cache is not None:
        cache[key] = result
    return result
