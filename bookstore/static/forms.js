document.querySelectorAll('form').forEach((form) => {
  const password = form.querySelector('[name="password"]');
  const confirmation = form.querySelector('[name="confirm_password"]');
  if (password && confirmation) {
    const validate = () => confirmation.setCustomValidity(
      password.value === confirmation.value ? '' : 'Passwords do not match.'
    );
    password.addEventListener('input', validate);
    confirmation.addEventListener('input', validate);
  }
});
document.querySelectorAll('img[data-cover-fallback]').forEach((image) => {
  image.addEventListener('error', () => {
    const fallback = image.dataset.coverFallback;
    if (image.getAttribute('src') !== fallback) image.src = fallback;
  });
});
document.querySelectorAll('form').forEach((form) => {
  const min = form.querySelector('[name="min_price"]');
  const max = form.querySelector('[name="max_price"]');
  if (min && max) {
    const validate = () => max.setCustomValidity(
      min.value && max.value && Number(min.value) > Number(max.value)
        ? 'Maximum price must be at least minimum price.' : ''
    );
    min.addEventListener('input', validate);
    max.addEventListener('input', validate);
  }
});
