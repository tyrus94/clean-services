const menuToggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.main-nav');

if (menuToggle && nav) {
  menuToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
    menuToggle.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
  });
}

document.querySelectorAll('.main-nav a').forEach(link => {
  link.addEventListener('click', () => {
    if (nav) nav.classList.remove('open');
    if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
  });
});

document.querySelectorAll('[data-service]').forEach(link => {
  link.addEventListener('click', () => {
    const serviceSelect = document.querySelector('select[name="service"]');
    if (serviceSelect) serviceSelect.value = link.dataset.service;
  });
});

const bookingForm = document.getElementById('booking');
if (bookingForm) bookingForm.addEventListener('submit', event => {
  event.preventDefault();
  const formData = new FormData(bookingForm);
  const name = String(formData.get('name') || '').trim();
  const phone = String(formData.get('phone') || '').trim();
  const service = String(formData.get('service') || '').trim();
  const location = String(formData.get('location') || '').trim();
  const otherLocation = String(formData.get('other_location') || '').trim();
  const date = String(formData.get('date') || '').trim();
  const details = String(formData.get('details') || '').trim();
  const error = document.querySelector('.form-error');

  if (!name || !phone || !service || !location) {
    if (error) error.textContent = 'Please complete your name, phone number, service and location.';
    return;
  }
  if (error) error.textContent = '';
  const lines = [
    'Hello Cleaning Services Kenya, I would like to request a cleaning quote.',
    '',
    `Name: ${name}`,
    `My phone number: ${phone}`,
    `Service: ${service}`,
    `Property location: ${location}`,
  ];
  if (otherLocation) {
    lines.push(`Other town / location: ${otherLocation}`);
  }
  lines.push(
    `Preferred date: ${date || 'Not specified'}`,
    `Additional details: ${details || 'None provided'}`,
    '',
    'Please let me know availability and the next steps. Thank you.'
  );
  const message = lines.join('\n');

  window.open(`https://wa.me/254706855633?text=${encodeURIComponent(message)}`, '_blank', 'noopener');
});

const yearElement = document.getElementById('year');
if (yearElement) yearElement.textContent = new Date().getFullYear();

const otherLocationSelect = document.querySelector('select[name="other_location"]');
if (otherLocationSelect) {
  otherLocationSelect.addEventListener('change', () => {
    const locInput = document.querySelector('input[name="location"]');
    if (locInput && otherLocationSelect.value && otherLocationSelect.value !== 'Other / Not listed') {
      locInput.value = otherLocationSelect.value;
    }
  });
}
