// Show/hide "other" fields conditionally
const industrySelect = document.querySelector('#id_industry');
const industryOtherWrap = document.querySelector('#industryOtherWrap');

// Client type toggle — show/hide company & industry for private clients
const clientTypeRadios = document.querySelectorAll('input[name="client_type"]');
const companyField = document.querySelector('#companyField');
const industryField = document.querySelector('#industryField');

if (clientTypeRadios.length) {
  const toggle = () => {
    const selected = document.querySelector('input[name="client_type"]:checked');
    const isPrivate = selected && selected.value === 'private';

    if (companyField) {
      companyField.style.display = isPrivate ? 'none' : 'flex';
      const input = companyField.querySelector('input');
      if (input) input.required = !isPrivate;
    }
    if (industryField) {
      industryField.style.display = isPrivate ? 'none' : 'flex';
      const select = industryField.querySelector('select');
      if (select) select.required = !isPrivate;
    }
  };
  clientTypeRadios.forEach(r => r.addEventListener('change', toggle));
  toggle();
}

if (industrySelect && industryOtherWrap) {
  const toggle = () => {
    industryOtherWrap.style.display = industrySelect.value === 'other' ? 'flex' : 'none';
  };
  industrySelect.addEventListener('change', toggle);
  toggle();
}

// Product "other" checkbox
const productCheckboxes = document.querySelectorAll('.checkbox-grid input[type="checkbox"]');
const productOtherWrap = document.querySelector('#productOtherWrap');
if (productCheckboxes.length && productOtherWrap) {
  const toggle = () => {
    const otherChecked = Array.from(productCheckboxes).some(cb => cb.value === 'other' && cb.checked);
    productOtherWrap.style.display = otherChecked ? 'flex' : 'none';
  };
  productCheckboxes.forEach(cb => cb.addEventListener('change', toggle));
  toggle();
}

// Existing supplier notes
const supplierCheckbox = document.querySelector('#id_existing_supplier');
const supplierNotesWrap = document.querySelector('#supplierNotesWrap');
if (supplierCheckbox && supplierNotesWrap) {
  const toggle = () => {
    supplierNotesWrap.style.display = supplierCheckbox.checked ? 'flex' : 'none';
  };
  supplierCheckbox.addEventListener('change', toggle);
  toggle();
}

// Animate form groups in on load
document.querySelectorAll('.form-group').forEach((el, i) => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(16px)';
  el.style.transition = `opacity 0.4s ease ${i * 0.05}s, transform 0.4s ease ${i * 0.05}s`;
  requestAnimationFrame(() => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });
});
