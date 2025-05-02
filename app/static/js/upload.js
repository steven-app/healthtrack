document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const dataSourceSelect = document.getElementById('dataSource');
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');
    const fileInfo = document.getElementById('fileInfo');
    
    // Hide progress section initially
    progressSection.style.display = 'none';

    // File input change handler
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            validateAndShowFileInfo(file);
        }
    });

    // Form submit handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        const formData = new FormData(form);
        await uploadFile(formData);
    });

    // Validate file and show file information
    function validateAndShowFileInfo(file) {
        const supportedFormats = {
            'zip': 'application/zip',
            'xml': 'text/xml',
            'csv': 'text/csv'
        };

        const fileExtension = file.name.split('.').pop().toLowerCase();
        const isValidFormat = Object.keys(supportedFormats).includes(fileExtension);

        if (!isValidFormat) {
            showError('Please upload a supported file format (ZIP, XML, or CSV)');
            fileInput.value = '';
            fileInfo.innerHTML = '';
            return false;
        }

        // Show file information
        const fileSizeInMB = (file.size / (1024 * 1024)).toFixed(2);
        fileInfo.innerHTML = `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${fileSizeInMB} MB</span>
            </div>
        `;

        return true;
    }

    // Validate form before submission
    function validateForm() {
        if (!dataSourceSelect.value) {
            showError('Please select a data source');
            return false;
        }

        if (!fileInput.files[0]) {
            showError('Please select a file to upload');
            return false;
        }

        return validateAndShowFileInfo(fileInput.files[0]);
    }

    // Upload file with progress tracking
    async function uploadFile(formData) {
        try {
            progressSection.style.display = 'block';
            updateProgress(0, 'Starting upload...');

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.message || 'Upload failed with status: ' + response.status);
            }

            const result = await response.json();
            
            if (result.success) {
                updateProgress(100, 'Upload complete!');
                showSuccess('File uploaded and processed successfully');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 2000);
            } else {
                throw new Error(result.message || 'Upload failed');
            }

        } catch (error) {
            console.error('Upload error:', error);
            showError(error.message || 'An error occurred during upload');
            progressSection.style.display = 'none';
        }
    }

    // Update progress bar and status
    function updateProgress(percent, status) {
        progressBar.style.width = `${percent}%`;
        progressBar.setAttribute('aria-valuenow', percent);
        progressStatus.textContent = status;
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'upload-error';
        errorDiv.textContent = message;
        
        const existingError = document.querySelector('.upload-error');
        if (existingError) {
            existingError.remove();
        }
        
        form.insertAdjacentElement('beforeend', errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }

    // Show success message
    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'upload-success';
        successDiv.textContent = message;
        
        const existingSuccess = document.querySelector('.upload-success');
        if (existingSuccess) {
            existingSuccess.remove();
        }
        
        form.insertAdjacentElement('beforeend', successDiv);
    }
}); 