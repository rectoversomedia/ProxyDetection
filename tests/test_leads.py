"""Tests for lead management."""

import pytest
import tempfile
import json
import csv
from pathlib import Path

from src.leads.parser import LeadParser, ParseResult
from src.leads.validator import LeadValidator, ValidationResult
from src.leads.generator import LeadGenerator, LeadGeneratorConfig


class TestLeadParser:
    """Tests for LeadParser."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = LeadParser()
        assert parser is not None

    def test_parse_csv(self):
        """Test CSV parsing."""
        parser = LeadParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email"])
            writer.writeheader()
            writer.writerow({"name": "John Doe", "email": "john@example.com"})
            writer.writerow({"name": "Jane Doe", "email": "jane@example.com"})
            temp_path = f.name

        try:
            result = parser.parse_csv(Path(temp_path))

            assert result.total_rows == 2
            assert len(result.leads) == 2
            assert result.leads[0]["name"] == "John Doe"
        finally:
            Path(temp_path).unlink()

    def test_parse_json(self):
        """Test JSON parsing."""
        parser = LeadParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([
                {"name": "John Doe", "email": "john@example.com"},
                {"name": "Jane Doe", "email": "jane@example.com"},
            ], f)
            temp_path = f.name

        try:
            result = parser.parse_json(Path(temp_path))

            assert result.total_rows == 2
            assert len(result.leads) == 2
        finally:
            Path(temp_path).unlink()

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises error."""
        parser = LeadParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/file.csv")

    def test_normalize_key(self):
        """Test key normalization."""
        parser = LeadParser()

        assert parser._normalize_key("First Name") == "first_name"
        assert parser._normalize_key("E-mail") == "e_mail"
        assert parser._normalize_key("Phone Number") == "phone_number"


class TestLeadValidator:
    """Tests for LeadValidator."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = LeadValidator()
        assert validator is not None

    def test_validate_valid_lead(self, sample_lead):
        """Test validating a valid lead."""
        validator = LeadValidator()
        is_valid, errors = validator.validate(sample_lead)

        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_email(self):
        """Test validation with missing email."""
        validator = LeadValidator()
        is_valid, errors = validator.validate({"name": "John"})

        assert not is_valid
        assert len(errors) > 0

    def test_validate_invalid_email(self):
        """Test validation with invalid email."""
        validator = LeadValidator()
        is_valid, errors = validator.validate({
            "name": "John",
            "email": "not-an-email"
        })

        assert not is_valid
        assert any("email" in e.lower() for e in errors)

    def test_validate_full(self, sample_lead):
        """Test full validation result."""
        validator = LeadValidator()
        result = validator.validate_full(sample_lead)

        assert isinstance(result, ValidationResult)
        assert result.is_valid

    def test_validate_batch(self, sample_leads):
        """Test batch validation."""
        validator = LeadValidator()
        results = validator.validate_batch(sample_leads)

        assert len(results) == len(sample_leads)
        assert all(isinstance(r, ValidationResult) for r in results)


class TestLeadGenerator:
    """Tests for LeadGenerator."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        gen = LeadGenerator()
        assert gen is not None

    def test_generator_with_seed(self):
        """Test generator with seed."""
        gen1 = LeadGenerator(seed=123)
        gen2 = LeadGenerator(seed=123)

        lead1 = gen1.generate(LeadGeneratorConfig(country="US"))
        lead2 = gen2.generate(LeadGeneratorConfig(country="US"))

        assert lead1["email"] == lead2["email"]

    def test_generate_lead(self):
        """Test generating a single lead."""
        gen = LeadGenerator(seed=42)
        config = LeadGeneratorConfig(country="US")
        lead = gen.generate(config)

        assert "name" in lead
        assert "email" in lead
        assert "@" in lead["email"]
        assert lead["country"] == "US"

    def test_generate_lead_without_phone(self):
        """Test generating lead without phone."""
        gen = LeadGenerator(seed=42)
        config = LeadGeneratorConfig(country="US", include_phone=False)
        lead = gen.generate(config)

        assert "phone" not in lead

    def test_generate_batch(self):
        """Test generating multiple leads."""
        gen = LeadGenerator(seed=42)
        leads = gen.generate_batch(count=5, country="US")

        assert len(leads) == 5
        assert all("email" in lead for lead in leads)

    def test_generate_different_countries(self):
        """Test generating leads for different countries."""
        gen = LeadGenerator(seed=42)

        for country in ["US", "GB", "JP", "DE"]:
            lead = gen.generate(LeadGeneratorConfig(country=country))
            assert lead["country"] == country

    def test_email_format(self):
        """Test generated email format."""
        gen = LeadGenerator(seed=42)
        lead = gen.generate(LeadGeneratorConfig(country="US"))

        assert "@" in lead["email"]
        assert "." in lead["email"].split("@")[1]

    def test_phone_format(self):
        """Test generated phone format."""
        gen = LeadGenerator(seed=42)
        lead = gen.generate(LeadGeneratorConfig(country="US", include_phone=True))

        assert "phone" in lead
        assert lead["phone"].startswith("+1-")

    def test_export_to_json(self):
        """Test exporting leads to JSON."""
        gen = LeadGenerator(seed=42)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            count = gen.export_to_file(temp_path, count=3, country="US", format="json")

            assert count == 3
            with open(temp_path) as f:
                data = json.load(f)
                assert len(data) == 3
        finally:
            Path(temp_path).unlink()
