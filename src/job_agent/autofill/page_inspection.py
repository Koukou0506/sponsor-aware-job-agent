from typing import Any

from job_agent.autofill.models import DetectedField

_DETECT_SCRIPT = r"""
(elements) => {
  const cssEscape = (value) => {
    if (window.CSS && CSS.escape) return CSS.escape(value);
    return value.replace(/[^a-zA-Z0-9_-]/g, (match) => `\\${match}`);
  };
  const pathFor = (element) => {
    if (element.id) return `#${cssEscape(element.id)}`;
    const parts = [];
    let node = element;
    while (node && node.nodeType === Node.ELEMENT_NODE && parts.length < 6) {
      let part = node.tagName.toLowerCase();
      if (node.getAttribute('name')) {
        part += `[name="${cssEscape(node.getAttribute('name'))}"]`;
        parts.unshift(part);
        break;
      }
      const siblings = Array.from(node.parentElement?.children || [])
        .filter((item) => item.tagName === node.tagName);
      if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
      parts.unshift(part);
      node = node.parentElement;
    }
    return parts.join(' > ');
  };
  return elements
    .filter((element) => {
      const style = window.getComputedStyle(element);
      const type = (element.getAttribute('type') || '').toLowerCase();
      const rect = element.getBoundingClientRect();
      return !element.disabled && type !== 'hidden' && type !== 'submit' &&
        style.display !== 'none' && style.visibility !== 'hidden' &&
        rect.width > 0 && rect.height > 0;
    })
    .map((element) => {
      const id = element.id || '';
      const explicit = id
        ? document.querySelector(`label[for="${cssEscape(id)}"]`)?.innerText || ''
        : '';
      const enclosing = element.closest('label')?.innerText || '';
      const aria = element.getAttribute('aria-label') || '';
      const container = element.closest('fieldset, [data-question], .field, .form-field, div');
      const nearby = (container?.innerText || '').trim().slice(0, 500);
      const options = element.tagName.toLowerCase() === 'select'
        ? Array.from(element.options).map((option) => option.text.trim())
        : [];
      const maxLength = Number.parseInt(element.getAttribute('maxlength') || '', 10);
      return {
        selector: pathFor(element),
        tag: element.tagName.toLowerCase(),
        input_type: element.getAttribute('type'),
        ats_field_id: id || element.getAttribute('data-field-id'),
        label: (explicit || enclosing || aria).trim(),
        name: element.getAttribute('name') || '',
        placeholder: element.getAttribute('placeholder') || '',
        nearby_text: nearby,
        required: element.required || element.getAttribute('aria-required') === 'true',
        max_length: Number.isFinite(maxLength) && maxLength > 0 ? maxLength : null,
        options,
      };
    });
}
"""


async def detect_visible_fields(
    page: Any,
    *,
    form_selector: str = "form",
) -> list[DetectedField]:
    form_selectors = [
        item.strip() for item in form_selector.split(",") if item.strip()
    ]
    selector = ", ".join(
        f"{item} {control}"
        for item in form_selectors
        for control in ("input", "textarea", "select")
    )
    elements = page.locator(selector)
    payload = await elements.evaluate_all(_DETECT_SCRIPT)
    return [DetectedField.model_validate(item) for item in payload]


async def body_text(page: Any) -> str:
    return str(await page.locator("body").inner_text())
