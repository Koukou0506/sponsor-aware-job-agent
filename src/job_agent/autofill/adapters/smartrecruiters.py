from job_agent.autofill.adapters.base import BaseFormAdapter


class SmartRecruitersFormAdapter(BaseFormAdapter):
    platform = "smartrecruiters"
    form_selector = "form[data-testid='application-form'], form[action*='apply']"
