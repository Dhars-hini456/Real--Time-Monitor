// Online Certificate Portal - Frontend Interactivity

document.addEventListener("DOMContentLoaded", function () {

    // Auto-hide alerts after 5 seconds
    document.querySelectorAll(".alert").forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Password confirmation validation on registration form
    const regForm = document.getElementById("registerForm");
    if (regForm) {
        regForm.addEventListener("submit", function (e) {
            const pwd = document.getElementById("password").value;
            const confirm = document.getElementById("confirm_password").value;
            if (pwd !== confirm) {
                e.preventDefault();
                alert("Passwords do not match. Please re-check.");
            }
        });
    }

    // Dynamic document upload rows on the "Apply Certificate" form
    const addDocBtn = document.getElementById("addDocumentRow");
    const docContainer = document.getElementById("documentsContainer");
    if (addDocBtn && docContainer) {
        addDocBtn.addEventListener("click", function () {
            const row = document.createElement("div");
            row.className = "doc-upload-row row g-2 align-items-center";
            row.innerHTML = `
                <div class="col-md-5">
                    <select class="form-select" name="doc_type" required>
                        <option value="">-- Select Document Type --</option>
                        ${window.DOC_TYPES.map(t => `<option value="${t}">${t}</option>`).join("")}
                    </select>
                </div>
                <div class="col-md-6">
                    <input type="file" class="form-control" name="documents" accept=".pdf,.png,.jpg,.jpeg" required>
                </div>
                <div class="col-md-1 text-end">
                    <button type="button" class="btn btn-sm btn-outline-danger remove-doc-row"><i class="fa-solid fa-trash"></i></button>
                </div>`;
            docContainer.appendChild(row);
        });

        docContainer.addEventListener("click", function (e) {
            if (e.target.closest(".remove-doc-row")) {
                e.target.closest(".doc-upload-row").remove();
            }
        });
    }

    // Certificate type change -> show/hide income field
    const certTypeSelect = document.getElementById("cert_type");
    const incomeField = document.getElementById("incomeFieldWrapper");
    if (certTypeSelect && incomeField) {
        function toggleIncome() {
            if (certTypeSelect.value === "Income Certificate") {
                incomeField.classList.remove("d-none");
            } else {
                incomeField.classList.add("d-none");
            }
        }
        certTypeSelect.addEventListener("change", toggleIncome);
        toggleIncome();
    }

    // Officer/Admin approve-reject confirmation
    document.querySelectorAll(".confirm-action").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            const msg = btn.getAttribute("data-confirm") || "Are you sure?";
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // Simple print button for certificate detail page
    const printBtn = document.getElementById("printCertBtn");
    if (printBtn) {
        printBtn.addEventListener("click", function () {
            window.print();
        });
    }
});
