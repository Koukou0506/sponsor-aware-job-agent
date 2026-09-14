from job_agent.autofill.adapters.base import BaseFormAdapter


class GreenhouseFormAdapter(BaseFormAdapter):
    platform = "greenhouse"
    form_selector = "form#application_form, form[action*='applications']"
