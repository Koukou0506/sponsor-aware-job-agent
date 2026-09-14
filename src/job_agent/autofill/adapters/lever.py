from job_agent.autofill.adapters.base import BaseFormAdapter


class LeverFormAdapter(BaseFormAdapter):
    platform = "lever"
    form_selector = "form.application-form, form[action*='/apply']"
