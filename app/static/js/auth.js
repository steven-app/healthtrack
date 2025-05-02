document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });

    // Password strength meter and requirements
    const passwordInput = document.querySelector('input[type="password"]');
    if (passwordInput) {
        const requirements = {
            length: { regex: /.{8,}/, text: 'At least 8 characters' },
            letter: { regex: /[A-Za-z]/, text: 'At least one letter' },
            number: { regex: /[0-9]/, text: 'At least one number' },
            special: { regex: /[@$!%*#?&]/, text: 'At least one special character' }
        };

        // Create requirements list
        const requirementsList = document.createElement('ul');
        requirementsList.className = 'password-requirements';
        Object.keys(requirements).forEach(req => {
            const li = document.createElement('li');
            li.id = `req-${req}`;
            li.textContent = requirements[req].text;
            requirementsList.appendChild(li);
        });
        passwordInput.parentNode.appendChild(requirementsList);

        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            
            // Check requirements
            Object.keys(requirements).forEach(req => {
                const li = document.getElementById(`req-${req}`);
                if (requirements[req].regex.test(password)) {
                    li.classList.add('valid');
                    li.classList.remove('invalid');
                    strength++;
                } else {
                    li.classList.add('invalid');
                    li.classList.remove('valid');
                }
            });
            
            // Update strength meter
            const strengthMeter = document.querySelector('.password-strength-meter');
            if (strengthMeter) {
                strengthMeter.style.width = (strength * 25) + '%';
                strengthMeter.className = 'password-strength-meter';
                
                if (strength <= 2) {
                    strengthMeter.classList.add('bg-danger');
                } else if (strength <= 3) {
                    strengthMeter.classList.add('bg-warning');
                } else {
                    strengthMeter.classList.add('bg-success');
                }
            }
        });
    }

    // Email validation
    const emailInput = document.querySelector('input[type="email"]');
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const email = this.value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && !emailRegex.test(email)) {
                this.setCustomValidity('Please enter a valid email address');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}); 