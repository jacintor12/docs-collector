function deleteDocument(caseId, filename) {
    if (!confirm(`Delete document '${filename}'? This cannot be undone.`)) return;
    fetch(`/api/cases/${caseId}/documents/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        alert(result.message || result.error);
        loadDocumentsList(caseId);
    });
}
let currentCaseId = null;

function showDocumentsModal(caseId, caseNumber) {
    currentCaseId = caseId;
    document.getElementById('documents-modal').style.display = 'flex';
    document.getElementById('modal-case-number').textContent = caseNumber;
    loadDocumentsList(caseId);
    document.getElementById('upload-status').textContent = '';

    // Setup drag-and-drop and upload listeners each time modal is opened
    const uploadArea = document.getElementById('upload-area');
    const uploadInput = document.getElementById('upload-input');
    if (uploadArea && uploadInput) {
        uploadArea.onclick = () => uploadInput.click();
        uploadArea.ondragover = e => {
            e.preventDefault();
            uploadArea.style.background = '#e3f2fd';
        };
        uploadArea.ondragleave = e => {
            e.preventDefault();
            uploadArea.style.background = '';
        };
        uploadArea.ondrop = e => {
            e.preventDefault();
            uploadArea.style.background = '';
            handleFilesUpload(e.dataTransfer.files);
        };
        uploadInput.onchange = e => {
            handleFilesUpload(e.target.files);
        };
    }
}

function closeDocumentsModal() {
    document.getElementById('documents-modal').style.display = 'none';
    currentCaseId = null;
}

function loadDocumentsList(caseId) {
    fetch(`/api/cases/${caseId}/documents`)
        .then(response => response.json())
        .then(docs => {
            const listDiv = document.getElementById('documents-list');
            if (docs.length === 0) {
                listDiv.innerHTML = '<em>No documents found.</em>';
                return;
            }
            listDiv.innerHTML = '<ul style="padding-left:1em;">' +
                docs.map(d => `
                    <li>
                        <span>${d.document_name}</span>
                        <a href="/api/cases/${caseId}/documents/${encodeURIComponent(d.document_name)}" download style="margin-left:1em;">Download</a>
                        <button style="margin-left:1em;" onclick="deleteDocument(${caseId}, '${d.document_name}')">Delete</button>
                    </li>
                `).join('') + '</ul>';
        });
}

function handleFilesUpload(files) {
    if (!currentCaseId) return;
    const statusDiv = document.getElementById('upload-status');
    statusDiv.textContent = '';
    Array.from(files).forEach(file => {
        const formData = new FormData();
        formData.append('file', file);
        fetch(`/api/cases/${currentCaseId}/documents/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.message) {
                statusDiv.textContent += `Uploaded: ${result.filename}\n`;
                loadDocumentsList(currentCaseId);
            } else {
                statusDiv.textContent += `Error: ${result.error}\n`;
            }
        })
        .catch(() => {
            statusDiv.textContent += `Error uploading ${file.name}\n`;
        });
    });
}

function deleteCase(caseId) {
    if (confirm('Are you sure you want to remove this case? It will no longer be displayed.')) {
        fetch(`/api/cases/${caseId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            alert('Case will no longer be displayed!');
            loadCases();
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadCases();
    document.getElementById('case-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const form = e.target;
        const data = {
            case_number: form.case_number.value,
            client_name: form.client_name.value,
            client_email: form.client_email.value,
            deadline_date: form.deadline_date.value,
            description: form.description.value
        };
        fetch('/api/cases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            alert(result.message || 'Case created!');
            loadCases();
            form.reset();
        });
    });
});
function makeEditableCell(value, onSave, type = 'text') {
    const td = document.createElement('td');
    if (type === 'date') {
        const input = document.createElement('input');
        input.type = 'date';
        // Ensure value is in YYYY-MM-DD format
        let dateVal = '';
        if (value) {
            const d = new Date(value);
            if (!isNaN(d)) {
                dateVal = d.toISOString().substring(0, 10);
            } else if (typeof value === 'string' && value.length >= 10) {
                dateVal = value.substring(0, 10);
            }
        }
        input.value = dateVal;
        input.onchange = () => onSave(input.value);
        td.appendChild(input);
    } else {
        const input = document.createElement('input');
        input.type = type;
        input.value = value || '';
        input.onblur = () => onSave(input.value);
        td.appendChild(input);
    }
    return td;
}

function loadCases() {
    fetch('/api/cases')
        .then(response => response.json())
        .then(cases => {
            const tbody = document.querySelector('#case-list tbody');
            tbody.innerHTML = '';
            if (!cases.length) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No cases found.</td></tr>';
                return;
            }
            cases.forEach(caseObj => {
                const deadline = new Date(caseObj.deadline_date);
                const now = new Date();
                let hoursRemaining = Math.max(0, Math.round((deadline - now) / 36e5));
                const tr = document.createElement('tr');

                // Editable Case # (narrow)
                const tdCaseNum = makeEditableCell(
                    caseObj.case_number || caseObj.case_id,
                    val => updateCaseField(caseObj.case_id, 'case_number', val)
                );
                tdCaseNum.style.width = '80px';
                tr.appendChild(tdCaseNum);
                // Editable Name
                tr.appendChild(makeEditableCell(
                    caseObj.client_name,
                    val => updateCaseField(caseObj.case_id, 'client_name', val)
                ));
                // Editable Email
                tr.appendChild(makeEditableCell(
                    caseObj.client_email,
                    val => updateCaseField(caseObj.case_id, 'client_email', val)
                ));
                // Editable Deadline
                tr.appendChild(makeEditableCell(
                    caseObj.deadline_date ? caseObj.deadline_date.substring(0, 10) : '',
                    val => updateCaseField(caseObj.case_id, 'deadline_date', val, tr),
                    'date'
                ));
                // Hours Remaining (narrow, color coded)
                const tdHours = document.createElement('td');
                tdHours.style.padding = '8px';
                tdHours.style.border = '1px solid #ddd';
                tdHours.style.width = '80px';
                tdHours.textContent = hoursRemaining;
                if (hoursRemaining < 24) {
                    tdHours.style.background = '#f8d7da';
                    tdHours.style.color = '#721c24';
                } else if (hoursRemaining < 72) {
                    tdHours.style.background = '#fff3cd';
                    tdHours.style.color = '#856404';
                } else {
                    tdHours.style.background = '#d4edda';
                    tdHours.style.color = '#155724';
                }
                tr.appendChild(tdHours);
                // Editable Description
                tr.appendChild(makeEditableCell(
                    caseObj.description || '',
                    val => updateCaseField(caseObj.case_id, 'description', val)
                ));
                // Delete button
                const tdDelete = document.createElement('td');
                tdDelete.style.padding = '8px';
                tdDelete.style.border = '1px solid #ddd';
                tdDelete.innerHTML = `<button onclick="deleteCase(${caseObj.case_id})">Delete</button>`;
                tr.appendChild(tdDelete);
                // Documents button
                const tdDocs = document.createElement('td');
                tdDocs.style.padding = '8px';
                tdDocs.style.border = '1px solid #ddd';
                tdDocs.innerHTML = `<button onclick="showDocumentsModal(${caseObj.case_id}, '${caseObj.case_number || caseObj.case_id}')">View/Upload</button>`;
                tr.appendChild(tdDocs);
                tbody.appendChild(tr);
            });
        });
}

function updateCaseField(caseId, field, value, tr) {
    const data = {};
    data[field] = value;
    fetch(`/api/cases/${caseId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(() => {
        if (field === 'deadline_date' && tr) {
            // Update hours remaining cell
            const deadline = new Date(value);
            const now = new Date();
            const hoursRemaining = Math.max(0, Math.round((deadline - now) / 36e5));
            tr.children[4].textContent = hoursRemaining;
        }
    });
}
