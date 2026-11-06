// SmartHire Client-side Interactions

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Applicant Ranking Table Live Filter
    const filterInput = document.getElementById("applicantSearchInput");
    const statusFilter = document.getElementById("applicantStatusFilter");
    const scoreFilter = document.getElementById("applicantScoreFilter");
    const applicantTable = document.getElementById("rankedApplicantsTable");

    if (applicantTable && (filterInput || statusFilter || scoreFilter)) {
        const rows = applicantTable.querySelectorAll("tbody tr");

        function applyFilters() {
            const query = filterInput ? filterInput.value.toLowerCase().trim() : "";
            const statusVal = statusFilter ? statusFilter.value.toLowerCase() : "all";
            const scoreVal = scoreFilter ? scoreFilter.value : "all";

            rows.forEach(row => {
                const name = row.getAttribute("data-name") || "";
                const skills = row.getAttribute("data-skills") || "";
                const status = (row.getAttribute("data-status") || "").toLowerCase();
                const score = parseInt(row.getAttribute("data-score") || "0", 10);

                const matchesQuery = !query || name.toLowerCase().includes(query) || skills.toLowerCase().includes(query);
                const matchesStatus = statusVal === "all" || status.includes(statusVal);
                
                let matchesScore = true;
                if (scoreVal === "high") {
                    matchesScore = score >= 70;
                } else if (scoreVal === "medium") {
                    matchesScore = score >= 40 && score < 70;
                } else if (scoreVal === "low") {
                    matchesScore = score < 40;
                }

                if (matchesQuery && matchesStatus && matchesScore) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        }

        if (filterInput) filterInput.addEventListener("input", applyFilters);
        if (statusFilter) statusFilter.addEventListener("change", applyFilters);
        if (scoreFilter) scoreFilter.addEventListener("change", applyFilters);
    }
});

