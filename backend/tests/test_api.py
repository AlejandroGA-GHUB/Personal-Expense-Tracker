"""
Tests for the HTTP API - routing, categories, transactions and reports
"""
from app.models import Category, CategoryKeyword, Transaction


class TestRouting:
    def test_health_check(self, client):
        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_path_without_trailing_slash_still_resolves(self, client):
        # Regression: a catch-all SPA route used to match "/api/categories" before
        # Starlette could issue its trailing-slash redirect, so the frontend's category
        # fetch 404'd and every auto-category badge rendered as "Unknown"
        response = client.get("/api/categories", follow_redirects=True)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_unknown_api_path_returns_json_not_html(self, client):
        response = client.get("/api/definitely-not-a-route")

        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/json")


class TestCategories:
    def test_list_returns_the_seeded_defaults(self, client):
        response = client.get("/api/categories/")

        assert response.status_code == 200
        assert len(response.json()) == 6

    def test_create_category(self, client):
        response = client.post("/api/categories/", json={"name": "Travel", "description": ""})

        assert response.status_code == 200
        assert response.json()["name"] == "Travel"

    def test_duplicate_name_is_rejected(self, client):
        # Category.name is UNIQUE, so the endpoint guards with get_category_by_name
        # rather than letting an IntegrityError surface as a 500
        client.post("/api/categories/", json={"name": "Travel", "description": ""})
        response = client.post("/api/categories/", json={"name": "Travel", "description": ""})

        assert response.status_code == 409

    def test_delete_reassigns_transactions_to_other(self, client, db, categories,
                                                    make_transaction):
        make_transaction("NORTHWIND", 30.0, "Shopping")
        make_transaction("GLOBEX STORE", 12.0, "Shopping")

        response = client.delete(f"/api/categories/{categories['Shopping']}")

        assert response.status_code == 200
        assert response.json()["transactions_reassigned"] == 2
        # The transactions survive, refiled rather than deleted
        assert db.query(Transaction).count() == 2
        assert all(t.category_id == categories["Other"] for t in db.query(Transaction).all())

    def test_delete_removes_the_categorys_learned_keywords(self, client, db, categories,
                                                           keyword_for):
        keyword_for("northwind", "Shopping")

        client.delete(f"/api/categories/{categories['Shopping']}")

        # Those mappings only meant "file this merchant under the category you removed"
        assert db.query(CategoryKeyword).count() == 0

    def test_other_cannot_be_deleted(self, client, categories):
        # It is both the reassignment target and the cascade's last resort
        response = client.delete(f"/api/categories/{categories['Other']}")

        assert response.status_code == 400

    def test_deleting_a_missing_category_404s(self, client):
        assert client.delete("/api/categories/9999").status_code == 404


class TestTransactions:
    def test_create_expense(self, client, categories):
        response = client.post("/api/transactions/", json={
            "description": "Coffee",
            "amount": -4.50,
            "date": "2025-01-15T10:00:00",
            "category_id": categories["Food & Dining"]
        })

        assert response.status_code == 200
        assert response.json()["amount"] == -4.50

    def test_positive_amount_is_rejected(self, client, categories):
        # This app tracks expenses only - income is refused rather than stored
        response = client.post("/api/transactions/", json={
            "description": "Paycheck",
            "amount": 1500.00,
            "date": "2025-01-15T10:00:00",
            "category_id": categories["Other"]
        })

        assert response.status_code == 422

    def test_patch_changes_category_and_learns(self, client, db, categories,
                                               make_transaction):
        transaction = make_transaction("NORTHWIND", 30.0, "Shopping", keywords="northwind")

        response = client.patch(f"/api/transactions/{transaction.id}",
                                json={"category_id": categories["Food & Dining"]})

        assert response.status_code == 200
        # A correction is what teaches stage 1, so it must outrank the model next time
        learned = db.query(CategoryKeyword).filter(
            CategoryKeyword.keyword == "northwind"
        ).first()
        assert learned is not None
        assert learned.category_id == categories["Food & Dining"]

    def test_filter_by_category(self, client, categories, make_transaction):
        make_transaction("NORTHWIND", 30.0, "Shopping")
        make_transaction("SHELL", 40.0, "Transportation")

        response = client.get("/api/transactions/filter",
                              params={"category_ids": categories["Shopping"]})

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestReports:
    def test_empty_database_returns_zeroes(self, client):
        assert client.get("/api/reports/daily_and_total_expenses").json() == [0.0, 0.0]

    def test_daily_average_divides_by_active_days(self, client, make_transaction):
        # Two purchases on one day and one on another: 3 rows, but only 2 active days
        make_transaction("A", 10.0, "Shopping", date="2025-01-05")
        make_transaction("B", 20.0, "Shopping", date="2025-01-05")
        make_transaction("C", 30.0, "Shopping", date="2025-01-06")

        average, total = client.get("/api/reports/daily_and_total_expenses").json()

        assert total == 60.0
        assert average == 30.0

    def test_monthly_reports_total_and_top_category(self, client, make_transaction):
        make_transaction("NORTHWIND", 30.0, "Food & Dining", date="2025-03-02")
        make_transaction("SHELL", 50.0, "Transportation", date="2025-03-05")

        total, top_category = client.get(
            "/api/reports/monthly", params={"month": 3, "year": 2025}
        ).json()

        assert total == 80.0
        assert top_category == ["Transportation", 50.0]

    def test_month_with_no_transactions(self, client):
        assert client.get("/api/reports/monthly",
                          params={"month": 7, "year": 2025}).json() == [0.0, []]

    def test_uncategorized_counts_toward_total_but_wins_no_category(self, client,
                                                                    make_transaction):
        make_transaction("MYSTERY", 22.75, None, date="2025-04-11")

        total, top_category = client.get(
            "/api/reports/monthly", params={"month": 4, "year": 2025}
        ).json()

        assert total == 22.75
        assert top_category == []

    def test_yearly_pads_empty_months(self, client, make_transaction):
        make_transaction("A", 10.0, "Shopping", date="2025-01-05")
        make_transaction("B", 20.0, "Shopping", date="2025-12-31")

        months, _ = client.get("/api/reports/yearly", params={"year": 2025}).json()

        assert len(months) == 12
        assert months[0] == 10.0
        assert months[11] == 20.0
        assert months[5] == 0.0

    def test_yearly_with_no_spending_returns_empty_list(self, client):
        months, _ = client.get("/api/reports/yearly", params={"year": 2019}).json()

        assert months == []

    def test_category_spending_is_ordered_highest_first(self, client, make_transaction):
        make_transaction("A", 10.0, "Shopping")
        make_transaction("B", 99.0, "Transportation")

        rows = client.get("/api/reports/category_spending").json()

        assert rows[0] == ["Transportation", 99.0]
        assert [name for name, _ in rows] == ["Transportation", "Shopping"]
