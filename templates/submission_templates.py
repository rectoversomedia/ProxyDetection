"""
Lead Submission Templates

This module contains templates for submitting leads to various platforms.
Each template defines the form structure and submission logic.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from ..browser.base import BaseBrowser


@dataclass
class FormField:
    """Represents a form field."""
    selector: str
    field_type: str  # input, select, textarea, checkbox, radio
    value_key: str  # Key in lead data
    required: bool = False
    wait_for: Optional[str] = None  # Selector to wait for before filling


@dataclass
class SubmissionTemplate:
    """Base template for lead submission."""
    name: str
    url: str
    fields: List[FormField]
    submit_selector: str
    success_selectors: List[str]  # Selectors that indicate success
    failure_selectors: List[str]  # Selectors that indicate failure
    wait_after_submit: float = 2.0
    retry_selector: Optional[str] = None


# =============================================================================
# Common Templates
# =============================================================================

GENERIC_LEAD_FORM = SubmissionTemplate(
    name="generic_lead_form",
    url="",
    fields=[
        FormField('input[name="name"]', "input", "name", required=True),
        FormField('input[name="email"]', "input", "email", required=True),
        FormField('input[name="phone"]', "input", "phone"),
        FormField('input[name="age"]', "input", "age"),
        FormField('select[name="country"]', "select", "country"),
        FormField('input[name="city"]', "input", "city"),
        FormField('input[name="state"]', "input", "state"),
        FormField('input[name="zip"]', "input", "zip_code"),
    ],
    submit_selector='button[type="submit"]',
    success_selectors=[
        ".success",
        ".thank-you",
        ".confirmation",
        "[class*='success']",
        "[class*='thank']",
        "#success",
    ],
    failure_selectors=[
        ".error",
        ".validation-error",
        "[class*='error']",
        "#error",
    ],
)


INSURANCE_LEAD_FORM = SubmissionTemplate(
    name="insurance_lead",
    url="",
    fields=[
        FormField('input[name="first_name"]', "input", "first_name", required=True),
        FormField('input[name="last_name"]', "input", "last_name", required=True),
        FormField('input[name="email"]', "input", "email", required=True),
        FormField('input[name="phone"]', "input", "phone", required=True),
        FormField('input[name="date_of_birth"]', "input", "date_of_birth"),
        FormField('select[name="gender"]', "select", "gender"),
        FormField('input[name="age"]', "input", "age"),
        FormField('select[name="state"]', "select", "state", required=True),
        FormField('input[name="zip_code"]', "input", "zip_code", required=True),
        FormField('input[name="coverage_amount"]', "input", "coverage_amount"),
    ],
    submit_selector='button[type="submit"], input[type="submit"]',
    success_selectors=[
        ".success-message",
        ".confirmation",
        "[data-success]",
        ".thank-you-page",
    ],
    failure_selectors=[
        ".error-message",
        ".validation",
        "[data-error]",
    ],
)


REAL_ESTATE_LEAD_FORM = SubmissionTemplate(
    name="real_estate_lead",
    url="",
    fields=[
        FormField('input[name="name"]', "input", "name", required=True),
        FormField('input[name="email"]', "input", "email", required=True),
        FormField('input[name="phone"]', "input", "phone", required=True),
        FormField('select[name="property_type"]', "select", "property_type"),
        FormField('select[name="budget"]', "select", "budget"),
        FormField('input[name="location"]', "input", "location"),
        FormField('select[name="bedrooms"]', "select", "bedrooms"),
        FormField('textarea[name="message"]', "textarea", "message"),
    ],
    submit_selector='button[type="submit"]',
    success_selectors=[
        ".success",
        ".enquiry-success",
        ".thank-you",
    ],
    failure_selectors=[
        ".error",
        ".form-error",
    ],
)


CONSULTATION_LEAD_FORM = SubmissionTemplate(
    name="consultation_lead",
    url="",
    fields=[
        FormField('input[name="full_name"]', "input", "name", required=True),
        FormField('input[name="email"]', "input", "email", required=True),
        FormField('input[name="phone"]', "input", "phone", required=True),
        FormField('select[name="service"]', "select", "service_type"),
        FormField('select[name="preferred_date"]', "select", "preferred_date"),
        FormField('textarea[name="notes"]', "textarea", "notes"),
    ],
    submit_selector='button.submit, input[type="submit"]',
    success_selectors=[
        ".success",
        ".booking-confirmed",
        "[class*='confirm']",
    ],
    failure_selectors=[
        ".error",
        ".alert-danger",
    ],
)


# =============================================================================
# Template Executor
# =============================================================================

class TemplateExecutor:
    """
    Executes a submission template against a browser page.
    """

    def __init__(self, template: SubmissionTemplate):
        """Initialize executor with template."""
        self.template = template

    async def execute(
        self,
        browser: BaseBrowser,
        lead_data: Dict[str, Any],
        custom_field_mapping: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the template against a browser page.

        Args:
            browser: Browser instance
            lead_data: Lead data dictionary
            custom_field_mapping: Override field mappings

        Returns:
            Result dictionary with success status and details
        """
        result = {
            "success": False,
            "message": "",
            "fields_filled": [],
            "fields_failed": [],
        }

        page = browser.get_page()
        field_mapping = custom_field_mapping or {}

        # Fill each field
        for field in self.template.fields:
            try:
                # Get value from lead data
                value_key = field_mapping.get(field.selector, field.value_key)
                value = self._get_lead_value(lead_data, value_key)

                if not value and field.required:
                    result["fields_failed"].append(f"{field.selector} (required, no value)")
                    continue

                if not value:
                    continue

                # Wait for field if needed
                if field.wait_for:
                    await browser.wait_for_selector(field.wait_for)

                # Fill based on field type
                if field.field_type == "input":
                    # Clear and fill
                    await page.fill(field.selector, "")
                    await asyncio.sleep(0.1)
                    await browser.fill(field.selector, str(value))
                    result["fields_filled"].append(field.selector)

                elif field.field_type == "select":
                    await browser.select_option(field.selector, str(value))
                    result["fields_filled"].append(field.selector)

                elif field.field_type == "textarea":
                    await browser.fill(field.selector, str(value))
                    result["fields_filled"].append(field.selector)

                elif field.field_type == "checkbox":
                    should_check = value in [True, "true", "yes", "1", 1]
                    is_checked = await page.is_checked(field.selector)
                    if should_check and not is_checked:
                        await browser.check(field.selector)
                    elif not should_check and is_checked:
                        await browser.uncheck(field.selector)
                    result["fields_filled"].append(field.selector)

                await asyncio.sleep(0.05)  # Small delay between fields

            except Exception as e:
                result["fields_failed"].append(f"{field.selector}: {str(e)}")

        # Submit form
        try:
            await page.click(self.template.submit_selector)
            await asyncio.sleep(self.template.wait_after_submit)

            # Check for success
            for selector in self.template.success_selectors:
                element = await page.query_selector(selector)
                if element:
                    result["success"] = True
                    result["message"] = f"Success indicator found: {selector}"
                    return result

            # Check for failure
            for selector in self.template.failure_selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    result["message"] = f"Failure indicator found: {text[:100]}"
                    return result

            # No clear indicator - assume success if no error
            result["success"] = True
            result["message"] = "Form submitted (no clear success/failure indicator)"

        except Exception as e:
            result["message"] = f"Submit failed: {str(e)}"

        return result

    def _get_lead_value(self, lead_data: Dict[str, Any], key: str) -> Any:
        """Get value from lead data with fallbacks."""
        # Direct match
        if key in lead_data:
            return lead_data[key]

        # Try common variations
        variations = [
            key,
            key.lower(),
            key.upper(),
            key.replace("_", ""),
            key.replace("-", ""),
            key.replace(" ", "_"),
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "zip_code",
            "postal_code",
        ]

        for var in variations:
            if var in lead_data:
                return lead_data[var]

        return None


# =============================================================================
# Template Registry
# =============================================================================

TEMPLATES: Dict[str, SubmissionTemplate] = {
    "generic": GENERIC_LEAD_FORM,
    "insurance": INSURANCE_LEAD_FORM,
    "real_estate": REAL_ESTATE_LEAD_FORM,
    "consultation": CONSULTATION_LEAD_FORM,
}


def get_template(name: str) -> Optional[SubmissionTemplate]:
    """Get a template by name."""
    return TEMPLATES.get(name.lower())


def list_templates() -> List[str]:
    """List available template names."""
    return list(TEMPLATES.keys())


def create_submit_script(
    template_name: str,
    target_url: str,
    field_overrides: Optional[Dict[str, str]] = None,
) -> Callable:
    """
    Create a submit script from a template.

    Args:
        template_name: Name of the template
        target_url: Target URL
        field_overrides: Override field selectors

    Returns:
        Async function for use as submit_script in SubmissionConfig
    """
    template = get_template(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")

    template.url = target_url

    if field_overrides:
        for field in template.fields:
            if field.selector in field_overrides:
                field.selector = field_overrides[field.selector]

    executor = TemplateExecutor(template)

    async def submit_script(browser, lead_data):
        result = await executor.execute(browser, lead_data)
        if not result["success"]:
            raise RuntimeError(f"Submission failed: {result['message']}")
        return result

    return submit_script
