"""
Tests for CSV parsing, bank format detection and merchant trimming

All merchants, reference numbers and addresses below are invented. They only need
to reproduce the *shape* of a real statement row - a merchant, then a reference
number, then an address - not any real one.
"""
import pytest

from app.utils.csv_parser import (
    detect_bank_format,
    parse_csv_auto_detect,
    strip_merchant_address,
)

APPLE_CARD_CSV = """Transaction Date,Clearing Date,Description,Merchant,Category,Type,Amount (USD),Purchased By
01/15/2025,01/16/2025,GLOBEX STORE* RB6T 1420 MAPLE AVENUE RIVERTON ZZ,Globex,Shopping,Purchase,42.50,Cardholder
01/16/2025,01/17/2025,NORTHWIND CAFE 88 CEDAR AVENUE RIVERTON ZZ,Northwind,Restaurants,Purchase,6.75,Cardholder
01/20/2025,01/21/2025,ACH DEPOSIT PAYMENT,Bank,Payment,Payment,-100.00,Cardholder
"""

BANK_OF_AMERICA_CSV = """Description,,Summary Amt.
Beginning balance as of 02/13/2025,,"794.57"

Date,Description,Amount,Running Bal.
02/13/2025,Beginning balance as of 02/13/2025,,"794.57"
02/14/2025,GLOBEX SHOP*RB6T 02/14 PURCHASE XXXXX00000 ZZ,-25.00,"769.57"
02/15/2025,PAYROLL DEPOSIT,1500.00,"2269.57"
"""


class TestStripMerchantAddress:
    """Cuts a description down to the merchant before keywords or the LLM see it"""

    @pytest.mark.parametrize("description,expected", [
        ("NORTHWIND MKT* ZQ4KP7VX8800 1420 MAPLE AVENUE RIVERTON 55555 ZZ USA",
         "NORTHWIND MKT* ZQ"),
        ("GLOBEX SHOP*RB6T 02/14 PURCHASE XXXXX00000 ZZ", "GLOBEX SHOP*RB"),
    ])
    def test_cuts_at_the_first_numeric_token(self, description, expected):
        assert strip_merchant_address(description) == expected

    def test_location_tokens_do_not_survive(self):
        # The whole point: address tokens should not exist to be learned
        trimmed = strip_merchant_address(
            "NORTHWIND MKT* ZQ4KP7VX8800 1420 MAPLE AVENUE RIVERTON 55555 ZZ USA"
        ).lower()

        assert "riverton" not in trimmed
        assert "maple" not in trimmed
        assert "usa" not in trimmed

    @pytest.mark.parametrize("description", [
        "599 LEXINGTON, LLC",
        "7-ELEVEN",
        "24 HOUR FITNESS",
    ])
    def test_merchants_leading_with_a_number_survive(self, description):
        # The scan starts at the second token, so a leading number is never the cut point
        assert strip_merchant_address(description).startswith(description.split()[0])

    def test_keeps_the_letter_prefix_of_a_numbered_token(self):
        # Dropping a token like "AIRLINE800" whole would lose the word identifying a
        # flight, which once cost the LLM the right answer
        trimmed = strip_merchant_address("TRAVELCO*BLUEJET AIRLINE800 CEDAR AVENUE")

        assert trimmed == "TRAVELCO*BLUEJET AIRLINE"

    def test_single_token_description_is_untouched(self):
        assert strip_merchant_address("NORTHWIND") == "NORTHWIND"

    def test_cuts_at_a_street_suffix(self):
        assert strip_merchant_address("JOES GARAGE MAIN STREET") == "JOES GARAGE MAIN"


class TestBankFormatDetection:
    def test_detects_apple_card(self):
        assert detect_bank_format(APPLE_CARD_CSV) == "apple_card"

    def test_detects_bank_of_america(self):
        assert detect_bank_format(BANK_OF_AMERICA_CSV) == "bank_of_america"

    def test_unknown_format_returns_none(self):
        assert detect_bank_format("Foo,Bar,Baz\n1,2,3\n") is None


class TestParsing:
    def test_apple_card_rows_are_parsed_and_signs_inverted(self, db):
        transactions = parse_csv_auto_detect(APPLE_CARD_CSV, "statement.csv", db)

        # The payment row is income once inverted, so it is dropped
        assert len(transactions) == 2
        assert all(transaction.amount < 0 for transaction in transactions)
        assert transactions[0].amount == -42.50

    def test_bank_of_america_income_row_is_dropped(self, db):
        transactions = parse_csv_auto_detect(BANK_OF_AMERICA_CSV, "statement.csv", db)

        assert len(transactions) == 1
        assert transactions[0].amount == -25.00

    def test_bank_category_is_carried_through(self, db):
        transactions = parse_csv_auto_detect(APPLE_CARD_CSV, "statement.csv", db)

        assert transactions[0].csv_category_name == "Shopping"

    def test_full_description_is_stored_untrimmed(self, db):
        # Only the keyword/LLM view is trimmed; the user still sees what the bank sent
        transactions = parse_csv_auto_detect(APPLE_CARD_CSV, "statement.csv", db)

        assert "RIVERTON" in transactions[0].description

    def test_every_row_reports_a_categorization_source(self, db):
        transactions = parse_csv_auto_detect(APPLE_CARD_CSV, "statement.csv", db)

        assert all(transaction.categorization_source for transaction in transactions)
