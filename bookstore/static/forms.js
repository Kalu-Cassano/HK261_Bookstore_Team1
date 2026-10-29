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
