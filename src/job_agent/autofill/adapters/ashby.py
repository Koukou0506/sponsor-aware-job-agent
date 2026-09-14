from job_agent.autofill.adapters.base import BaseFormAdapter


class AshbyFormAdapter(BaseFormAdapter):
    platform = "ashby"
    form_selector = "form[data-testid='application-form'], form"
