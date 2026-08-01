"""
Tests for the categorization cascade and adaptive learning
"""
from app.models import CategoryKeyword, Transaction
from app.utils.categorizer import (
    SOURCE_BANK,
    SOURCE_BUILTIN,
    SOURCE_LEARNED,
    SOURCE_NONE,
    _is_learnable,
    _keyword_category_map,
    auto_categorize_transaction,
    extract_keywords,
    learn_from_category_change,
    learn_from_import,
)


class TestCascadeOrdering:
    """Each stage should answer only when everything above it did not"""

    def test_stored_keywords_win_over_bank_category(self, db, categories, keyword_for):
        # A learned mapping is the user's own correction, so it outranks the bank's label
        keyword_for("northwind", "Entertainment")

        category_id, _, _, source = auto_categorize_transaction(
            db, "NORTHWIND GROCERY", -20.0, "Grocery"
        )

        assert source == SOURCE_LEARNED
        assert category_id == categories["Entertainment"]

    def test_bank_category_used_when_nothing_learned(self, db, categories):
        category_id, _, _, source = auto_categorize_transaction(
            db, "SOME UNKNOWN MERCHANT", -20.0, "Restaurants"
        )

        assert source == SOURCE_BANK
        assert category_id == categories["Food & Dining"]

    def test_builtin_keywords_used_when_bank_has_no_label(self, db, categories):
        # A Bank of America row carries no category at all, so stage 4 is what
        # keeps the whole file from importing as "Other"
        category_id, _, _, source = auto_categorize_transaction(
            db, "RIVERTON CAFE", -6.0, ""
        )

        assert source == SOURCE_BUILTIN
        assert category_id == categories["Food & Dining"]

    def test_falls_through_to_other(self, db, categories):
        category_id, _, suggestion, source = auto_categorize_transaction(
            db, "ZZQQ XYZZY", -5.0, ""
        )

        assert source == SOURCE_NONE
        assert category_id == categories["Other"]
        assert suggestion is None

    def test_unmappable_bank_label_never_claims_the_row(self, db, categories):
        # "Tolls" is a real label we have no mapping for, so stage 2 must not claim it
        _, _, _, source = auto_categorize_transaction(db, "FAIRVIEW FUEL", -25.0, "Tolls")

        assert source != SOURCE_BANK

    def test_unmappable_bank_label_offers_no_suggestion(self, db, categories):
        # The row falls to "Other" with nothing to apply, rather than reaching the LLM -
        # that is what stops one row showing two competing Apply buttons in the preview
        category_id, _, suggestion, source = auto_categorize_transaction(
            db, "ZZQQ XYZZY", -25.0, "Tolls"
        )

        assert category_id == categories["Other"]
        assert suggestion is None
        assert source == SOURCE_NONE

    def test_builtin_can_still_rescue_an_unmappable_label(self, db, categories):
        # Stage 4 is below stage 2 but still runs when stage 2 fails to map, so a
        # recognisable merchant is not thrown away just because its label was unknown
        category_id, _, _, source = auto_categorize_transaction(
            db, "FAIRVIEW FUEL", -25.0, "Tolls"
        )

        assert source == SOURCE_BUILTIN
        assert category_id == categories["Transportation"]


class TestBankLabelGate:
    """Only rows the bank left unlabelled are eligible for the LLM"""

    def test_other_is_treated_as_unlabelled(self, db, categories):
        # "Other" is the bank saying it did not know either, so stage 2 must not
        # claim the row - stage 4 gets a chance instead
        _, _, _, source = auto_categorize_transaction(db, "RIVERTON CAFE", -6.0, "Other")

        assert source == SOURCE_BUILTIN

    def test_na_is_treated_as_unlabelled(self, db, categories):
        _, _, _, source = auto_categorize_transaction(db, "RIVERTON CAFE", -6.0, "N/A")

        assert source == SOURCE_BUILTIN


class TestExtractKeywords:
    def test_strips_generic_transaction_words(self):
        keywords = extract_keywords("GLOBEX PURCHASE")

        assert "globex" in keywords
        assert "purchase" not in keywords

    def test_lowercases_tokens(self):
        assert all(keyword == keyword.lower() for keyword in extract_keywords("LOUD MERCHANT"))


class TestIsLearnable:
    """
    The concentration guard. A token is learnable only if every transaction
    carrying it shares one category.
    """

    def test_token_seen_in_one_category_is_learnable(self, db, categories, make_transaction):
        make_transaction("GLOBEX", 10.0, "Shopping", keywords="globex")
        make_transaction("GLOBEX", 20.0, "Shopping", keywords="globex")

        keyword_map = _keyword_category_map(db)

        assert _is_learnable("globex", categories["Shopping"], keyword_map) is True

    def test_token_spanning_categories_is_rejected(self, db, categories, make_transaction):
        # This is the "usa" case: an address token appears under everything
        make_transaction("GLOBEX USA", 10.0, "Shopping", keywords="globex,usa")
        make_transaction("CEDAR DINER USA", 20.0, "Food & Dining", keywords="diner,usa")

        keyword_map = _keyword_category_map(db)

        assert _is_learnable("usa", categories["Shopping"], keyword_map) is False
        assert _is_learnable("globex", categories["Shopping"], keyword_map) is True

    def test_unseen_token_is_trivially_learnable(self, db, categories):
        keyword_map = _keyword_category_map(db)

        assert _is_learnable("brandnew", categories["Shopping"], keyword_map) is True

    def test_is_not_frequency_based(self, db, categories, make_transaction):
        # 3 of 5 rows is a 60% share, which a frequency rule would likely reject on
        # a file this small, yet it is exactly the mapping worth keeping
        for _ in range(3):
            make_transaction("GLOBEX", 10.0, "Shopping", keywords="globex")
        make_transaction("DINER", 10.0, "Food & Dining", keywords="diner")
        make_transaction("SHELL", 10.0, "Transportation", keywords="shell")

        keyword_map = _keyword_category_map(db)

        assert _is_learnable("globex", categories["Shopping"], keyword_map) is True


class TestLearnFromCategoryChange:
    def test_correction_creates_keyword_for_new_category(self, db, categories, make_transaction):
        transaction = make_transaction("NORTHWIND", 30.0, "Shopping", keywords="northwind")

        learn_from_category_change(
            db, transaction.id, categories["Shopping"], categories["Food & Dining"]
        )

        mapping = db.query(CategoryKeyword).filter(
            CategoryKeyword.keyword == "northwind"
        ).first()
        assert mapping is not None
        assert mapping.category_id == categories["Food & Dining"]

    def test_address_token_is_not_learned(self, db, categories, make_transaction):
        # The measured failure: learning "usa" let one correction re-file a whole
        # statement, and correcting back relocated the poison instead of undoing it
        transaction = make_transaction("BLUEJET USA", 48.68, "Transportation",
                                       keywords="bluejet,usa")
        make_transaction("CEDAR DINER USA", 12.0, "Food & Dining", keywords="diner,usa")

        learn_from_category_change(
            db, transaction.id, categories["Transportation"], categories["Entertainment"]
        )

        learned = {row.keyword for row in db.query(CategoryKeyword).all()}
        assert "usa" not in learned
        assert "bluejet" in learned

    def test_decrement_removes_weight_from_old_category(self, db, categories,
                                                        make_transaction, keyword_for):
        keyword_for("northwind", "Shopping", weight=2)
        transaction = make_transaction("NORTHWIND", 30.0, "Shopping", keywords="northwind")

        learn_from_category_change(
            db, transaction.id, categories["Shopping"], categories["Food & Dining"]
        )

        old_mapping = db.query(CategoryKeyword).filter(
            CategoryKeyword.keyword == "northwind",
            CategoryKeyword.category_id == categories["Shopping"]
        ).first()
        assert old_mapping is None or old_mapping.weight < 2


class TestLearnFromImport:
    def test_only_llm_rows_are_learned(self, db, csv_row):
        # The other stages never called the model, so recording them saves nothing
        rows = [
            csv_row("MERCHANTA", 10.0, "Shopping", "merchanta", "llm"),
            csv_row("MERCHANTB", 10.0, "Shopping", "merchantb", "builtin_keywords"),
        ]

        learn_from_import(db, rows)

        learned = {row.keyword for row in db.query(CategoryKeyword).all()}
        assert "merchanta" in learned
        assert "merchantb" not in learned

    def test_second_pass_is_answered_by_stage_one(self, db, categories, csv_row):
        """A re-import of the same merchant should cost no model call"""
        row = csv_row("TRAVELCO", 48.68, "Entertainment", "travelco", "llm")
        learn_from_import(db, [row])

        category_id, _, _, source = auto_categorize_transaction(db, "TRAVELCO", -48.68, "")

        assert source == SOURCE_LEARNED
        assert category_id == categories["Entertainment"]

    def test_address_tokens_are_filtered_at_import(self, db, csv_row):
        # Auto-learning an address token would have taken "usa" to weight 51 on a real
        # statement, against a best real merchant token of 11
        rows = [
            csv_row("GLOBEX USA", 10.0, "Shopping", "globex,usa", "llm"),
            csv_row("CEDAR DINER USA", 10.0, "Food & Dining", "diner,usa", "llm"),
        ]

        learn_from_import(db, rows)

        learned = {row.keyword for row in db.query(CategoryKeyword).all()}
        assert "usa" not in learned
        assert "globex" in learned
