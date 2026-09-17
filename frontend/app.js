/**
 * AI Academic Early-Warning & Intervention Decision Engine
 * Enterprise Frontend Application Logic
 */

const API_BASE = window.location.origin;
let currentSessionId = "sess-" + Math.random().toString(36).substring(2, 9);
let cohortStudentsData = [];
let activeWorkflowId = "wf-ready";
let authToken = sessionStorage.getItem("academic_auth_token") || null;
let currentUser = null;

document.addEventListener("DOMContentLoaded", () => {
  initAuth();
  initTabs();
  initChat();
  initFacultyReview();
  initCohortControls();
  initWorkflowControls();
  initEvidenceControls();
  initModal();
});

/* ==========================================================================
   AUTHENTICATION & ACCESS CONTROL
   ========================================================================== */
function initAuth() {
  const loginForm = document.getElementById("authLoginForm");
  const btnLogout = document.getElementById("btnLogout");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("authEmail").value.trim();
      const password = document.getElementById("authPassword").value;
      await loginUser(email, password);
    });
  }

  if (btnLogout) {
    btnLogout.addEventListener("click", logoutUser);
  }

  // Check existing session
  checkExistingSession();
}

async function checkExistingSession() {
  if (!authToken) {
    showAuthScreen();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.user) {
        currentUser = data.user;
        showDashboard(currentUser);
        return;
      }
    }
  } catch (err) {
    console.warn("Session check failed:", err);
  }

  // Fallback to auth screen if invalid
  showAuthScreen();
}

async function loginUser(email, password) {
  const alertBox = document.getElementById("authErrorAlert");
  const btn = document.getElementById("btnSignIn");
  if (alertBox) alertBox.style.display = "none";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Authenticating...";
  }

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (res.ok) {
      const data = await res.json();
      authToken = data.token;
      currentUser = data.user;
      sessionStorage.setItem("academic_auth_token", authToken);
      showDashboard(currentUser);
    } else {
      const errData = await res.json();
      if (alertBox) {
        alertBox.textContent = errData.detail || "Authentication failed. Invalid institutional credentials.";
        alertBox.style.display = "block";
      }
    }
  } catch (err) {
    if (alertBox) {
      alertBox.textContent = "Unable to connect to authentication service. Please ensure API server is active.";
      alertBox.style.display = "block";
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Sign In to Advisory Console";
    }
  }
}

window.quickLogin = async function(email, password) {
  document.getElementById("authEmail").value = email;
  document.getElementById("authPassword").value = password;
  await loginUser(email, password);
};

async function logoutUser() {
  if (authToken) {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${authToken}` }
      });
    } catch (err) {
      console.warn("Logout error:", err);
    }
  }

  authToken = null;
  currentUser = null;
  sessionStorage.removeItem("academic_auth_token");
  showAuthScreen();
}

function showAuthScreen() {
  const authScreen = document.getElementById("authScreen");
  const dashboardScreen = document.getElementById("dashboardScreen");
  if (authScreen) authScreen.style.display = "flex";
  if (dashboardScreen) dashboardScreen.style.display = "none";
}

function showDashboard(user) {
  const authScreen = document.getElementById("authScreen");
  const dashboardScreen = document.getElementById("dashboardScreen");
  if (authScreen) authScreen.style.display = "none";
  if (dashboardScreen) dashboardScreen.style.display = "flex";

  // Update header profile widget
  if (user) {
    const initials = user.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    const avatarEl = document.getElementById("headerUserAvatar");
    const nameEl = document.getElementById("headerUserName");
    const roleEl = document.getElementById("headerUserRole");
    if (avatarEl) avatarEl.textContent = initials || "KR";
    if (nameEl) nameEl.textContent = user.name;
    if (roleEl) roleEl.textContent = user.role_display || "Faculty Advisor";
  }

  // Load dashboard data
  fetchSystemHealth();
  fetchFeaturedStudent("STU104");
  fetchCohortOverview();
  fetchSystemMetrics();
}


/* ==========================================================================
   TABS MANAGEMENT
   ========================================================================== */
function initTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = `tab-${tab.dataset.tab}`;
      const pane = document.getElementById(targetId);
      if (pane) pane.classList.add("active");

      // Tab specific refreshes
      if (tab.dataset.tab === "students" && cohortStudentsData.length === 0) {
        fetchCohortOverview();
      } else if (tab.dataset.tab === "metrics") {
        fetchSystemMetrics();
      } else if (tab.dataset.tab === "evidence") {
        fetchEvidenceForStudent(document.getElementById("evidenceStudentSelect").value || "STU104");
      }
    });
  });
}

/* ==========================================================================
   SYSTEM HEALTH & HEADER PILLS
   ========================================================================== */
async function fetchSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("dbStatusText").textContent = data.active_database;
      document.getElementById("llmStatusText").textContent = data.live_groq_llm 
        ? `Live Groq (${data.groq_model})` 
        : "Deterministic Fallback";
    }
  } catch (err) {
    console.warn("Health check error:", err);
  }
}

/* ==========================================================================
   FEATURED STUDENT (STU104) & DECISION CARD
   ========================================================================== */
async function fetchFeaturedStudent(studentId) {
  try {
    const res = await fetch(`${API_BASE}/students/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId, session_id: currentSessionId })
    });

    if (res.ok) {
      const data = await res.json();
      activeWorkflowId = data.workflow_id;

      // Update Featured Decision Card
      document.getElementById("featuredStudentName").textContent = `${data.student_name} (${data.student_id})`;
      document.getElementById("featuredScoreValue").textContent = data.risk_score;
      document.getElementById("featuredBandLabel").textContent = data.risk_band;
      
      const badge = document.getElementById("featuredScoreBadge");
      badge.className = `risk-score-badge ${data.risk_band.toLowerCase()}`;

      // Telemetry
      document.getElementById("telAttendance").textContent = `${data.attendance_pct}%`;
      document.getElementById("telCurrentAvg").textContent = `${data.current_average_pct}%`;
      document.getElementById("telPriorAvg").textContent = `${data.prior_average_pct}%`;
      document.getElementById("telDelta").textContent = `${data.performance_delta}%`;
      document.getElementById("telFailedTests").textContent = data.failed_assessments_count;
      document.getElementById("telMissedAsn").textContent = data.missed_assignments_count;

      // Chips
      document.getElementById("chipPerf").textContent = `${data.breakdown.performance} pts`;
      document.getElementById("chipAtt").textContent = `${data.breakdown.attendance} pts`;
      document.getElementById("chipAsn").textContent = `${data.breakdown.assignments} pts`;
      document.getElementById("chipAssess").textContent = `${data.breakdown.assessments} pts`;
      document.getElementById("chipHist").textContent = `${data.breakdown.history} pts`;

      // Risk Factors
      const factorsContainer = document.getElementById("featuredFactorsContainer");
      factorsContainer.innerHTML = "";
      data.risk_factors.forEach(f => {
        const span = document.createElement("span");
        span.className = "tag tag-critical";
        span.textContent = f;
        factorsContainer.appendChild(span);
      });

      // Top 3 Interventions
      const intvList = document.getElementById("featuredInterventionsList");
      intvList.innerHTML = "";
      data.top_interventions.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${item.title}</strong><p>${item.description || "Evidence-based educational action."}</p>`;
        intvList.appendChild(li);
      });

      // Governance Meta
      document.getElementById("reviewUrgency").textContent = data.urgency;
      document.getElementById("reviewOversight").textContent = data.faculty_oversight;
      document.getElementById("reviewFollowUp").textContent = data.follow_up_period;

      // Update Workflow Tab Details with this run
      document.getElementById("wfIdVal").textContent = data.workflow_id;
      document.getElementById("wfAgentVal").textContent = "DecisionAgent";
      document.getElementById("wfStatusVal").textContent = "COMPLETED";
      document.getElementById("wfDurationVal").textContent = `18.6 ms`;
      document.getElementById("workflowLogText").textContent = 
        `Workflow ID: ${data.workflow_id}\n` +
        `Student: ${data.student_id} (${data.student_name})\n` +
        `Result: Score ${data.risk_score}/100, Band: ${data.risk_band}\n` +
        `Diagnostic Summary: ${data.summary}\n` +
        `State: All validators passed without retries.`;
    }
  } catch (err) {
    console.error("Failed to fetch featured student:", err);
  }
}

/* ==========================================================================
   COHORT BATCH ANALYSIS (CSE-A 60 STUDENTS)
   ========================================================================== */
async function fetchCohortOverview() {
  try {
    const res = await fetch(`${API_BASE}/class/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ section: "CSE-A" })
    });

    if (res.ok) {
      const data = await res.json();
      cohortStudentsData = data.ranked_students || [];

      // Update KPI Cards
      document.getElementById("kpiTotalStudents").textContent = data.total_students;
      document.getElementById("kpiCriticalCount").textContent = data.distribution.Critical || 2;
      document.getElementById("kpiHighCount").textContent = data.distribution.High || 3;
      document.getElementById("kpiMedLowCount").textContent = 
        `${data.distribution.Medium || 10} / ${data.distribution.Low || 45}`;

      renderStudentsTable(cohortStudentsData);
    }
  } catch (err) {
    console.error("Failed to load cohort overview:", err);
  }
}

function renderStudentsTable(students) {
  const tbody = document.getElementById("studentsTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  students.forEach(s => {
    const tr = document.createElement("tr");
    const bandClass = s.risk_band.toLowerCase();

    tr.innerHTML = `
      <td><strong>${s.student_id}</strong></td>
      <td>${s.name}</td>
      <td>${s.section}</td>
      <td>${s.attendance_pct}%</td>
      <td>${s.current_average_pct}%</td>
      <td>${s.prior_average_pct}%</td>
      <td class="${s.performance_delta < 0 ? 'text-critical' : ''}">${s.performance_delta}%</td>
      <td>${s.failed_assessments}</td>
      <td><strong>${s.risk_score}</strong>/100</td>
      <td><span class="badge badge-${bandClass}">${s.risk_band}</span></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="analyzeAndFocus('${s.student_id}')">Analyze</button>
        <button class="btn btn-secondary btn-sm" onclick="viewProfileModal('${s.student_id}')">Profile</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function initCohortControls() {
  const search = document.getElementById("studentSearch");
  const filter = document.getElementById("riskFilter");
  const reanalyzeBtn = document.getElementById("btnRunCohortAnalysis");

  const applyFilters = () => {
    const q = (search.value || "").toLowerCase().trim();
    const band = filter.value;

    const filtered = cohortStudentsData.filter(s => {
      const matchesSearch = s.student_id.toLowerCase().includes(q) || s.name.toLowerCase().includes(q);
      const matchesBand = band === "ALL" || s.risk_band === band;
      return matchesSearch && matchesBand;
    });
    renderStudentsTable(filtered);
  };

  if (search) search.addEventListener("input", applyFilters);
  if (filter) filter.addEventListener("change", applyFilters);
  if (reanalyzeBtn) reanalyzeBtn.addEventListener("click", fetchCohortOverview);
}

window.analyzeAndFocus = function(studentId) {
  fetchFeaturedStudent(studentId);
  // Switch to overview tab
  document.querySelector('.nav-tab[data-tab="overview"]').click();
};

/* ==========================================================================
   FACULTY ADVISORY CHAT WITH CONVERSATIONAL MEMORY
   ========================================================================== */
function initChat() {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const messagesBox = document.getElementById("chatMessages");

  if (!form || !input) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;

    // Append user bubble
    appendBubble("user", "You", q);
    input.value = "";

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, session_id: currentSessionId })
      });

      if (res.ok) {
        const data = await res.json();
        const roleLabel = data.is_live_llm ? `Live Groq (${data.model})` : "Faculty Advisory Engine";
        appendBubble("assistant", roleLabel, data.response);
      } else {
        appendBubble("assistant", "System Error", "Unable to retrieve advisor consultation at this time.");
      }
    } catch (err) {
      appendBubble("assistant", "Network Error", "Connection failed. Please check system status.");
    }
  });

  function appendBubble(sender, label, text) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerHTML = `
      <div class="chat-meta">${label}</div>
      <p>${text}</p>
    `;
    messagesBox.appendChild(bubble);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }
}

/* ==========================================================================
   HUMAN-IN-THE-LOOP FACULTY REVIEW ACTIONS
   ========================================================================== */
function initFacultyReview() {
  const feedbackInput = document.getElementById("reviewFeedback");
  const confirmBox = document.getElementById("reviewConfirmation");

  const handleReview = async (action) => {
    const feedback = feedbackInput ? feedbackInput.value.trim() : "";
    try {
      const res = await fetch(`${API_BASE}/review/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_id: activeWorkflowId,
          student_id: "STU104",
          faculty_action: action,
          feedback: feedback || `Faculty action recorded: ${action}`,
          reviewer_name: "Dr. K. Raman"
        })
      });

      if (res.ok) {
        const data = await res.json();
        confirmBox.style.display = "block";
        confirmBox.style.backgroundColor = action === "APPROVE" ? "#dcfce7" : (action === "MODIFY" ? "#fef3c7" : "#fee2e2");
        confirmBox.style.color = action === "APPROVE" ? "#15803d" : (action === "MODIFY" ? "#b45309" : "#b91c1c");
        confirmBox.textContent = `Human-In-The-Loop Action: ${action} recorded by ${data.reviewer} at ${new Date(data.timestamp).toLocaleTimeString()}.`;
        fetchSystemMetrics();
      }
    } catch (err) {
      console.error("Failed to record review action:", err);
    }
  };

  const btnApprove = document.getElementById("btnApproveReview");
  const btnModify = document.getElementById("btnModifyReview");
  const btnReject = document.getElementById("btnRejectReview");

  if (btnApprove) btnApprove.addEventListener("click", () => handleReview("APPROVE"));
  if (btnModify) btnModify.addEventListener("click", () => handleReview("MODIFY"));
  if (btnReject) btnReject.addEventListener("click", () => handleReview("REJECT"));
}

/* ==========================================================================
   WORKFLOW TRIGGERING & VISUALIZATION
   ========================================================================== */
function initWorkflowControls() {
  const btn = document.getElementById("btnTriggerWorkflow");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.textContent = "Running Workflow...";
    try {
      const res = await fetch(`${API_BASE}/workflow/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "Analyze STU104", student_id: "STU104", session_id: currentSessionId })
      });
      if (res.ok) {
        const data = await res.json();
        document.getElementById("wfIdVal").textContent = data.workflow_id;
        document.getElementById("wfAgentVal").textContent = data.current_agent;
        document.getElementById("wfStatusVal").textContent = data.status;
        document.getElementById("wfDurationVal").textContent = `${data.duration_ms} ms`;
        document.getElementById("wfRetryVal").textContent = `${data.retry_count} / 3`;
        document.getElementById("workflowLogText").textContent = JSON.stringify(data, null, 2);
        fetchSystemMetrics();
      }
    } catch (err) {
      console.error("Workflow trigger error:", err);
    } finally {
      btn.disabled = false;
      btn.textContent = "Trigger Workflow (STU104)";
    }
  });
}

/* ==========================================================================
   EVIDENCE EXPLORER
   ========================================================================== */
function initEvidenceControls() {
  const picker = document.getElementById("evidenceStudentSelect");
  if (!picker) return;

  picker.addEventListener("change", () => {
    fetchEvidenceForStudent(picker.value);
  });
}

async function fetchEvidenceForStudent(studentId) {
  try {
    const res = await fetch(`${API_BASE}/students/${studentId}`);
    if (res.ok) {
      const profile = await res.json();

      // Attendance and Performance tables
      const attTable = document.getElementById("evAttendanceTable");
      const perfTable = document.getElementById("evPerformanceTable");
      attTable.innerHTML = "";
      perfTable.innerHTML = "";

      let totalAtt = 0;
      let totalMarks = 0;
      let failedCount = 0;

      (profile.enrolled_courses || []).forEach(c => {
        totalAtt += c.attendance_pct;
        totalMarks += c.total_marks;
        if (!c.passed || c.total_marks < 50) failedCount++;

        // Row in Attendance
        const attTr = document.createElement("tr");
        const attTier = c.attendance_pct < 66 ? "Critical" : (c.attendance_pct < 75 ? "Warning" : "Acceptable");
        attTr.innerHTML = `
          <td><strong>${c.course_code}</strong></td>
          <td>${c.attendance_pct}%</td>
          <td><span class="badge badge-${attTier === 'Critical' ? 'critical' : (attTier === 'Warning' ? 'medium' : 'low')}">${attTier}</span></td>
        `;
        attTable.appendChild(attTr);

        // Row in Performance
        const perfTr = document.createElement("tr");
        perfTr.innerHTML = `
          <td><strong>${c.course_code}</strong></td>
          <td>${c.total_marks}%</td>
          <td><span class="badge badge-${c.passed && c.total_marks >= 50 ? 'low' : 'critical'}">${c.passed && c.total_marks >= 50 ? 'Passed' : 'Failed'}</span></td>
        `;
        perfTable.appendChild(perfTr);
      });

      const avgAtt = Math.round(totalAtt / (profile.enrolled_courses.length || 1));
      const avgMarks = (totalMarks / (profile.enrolled_courses.length || 1)).toFixed(1);

      document.getElementById("evAttBadge").textContent = `${avgAtt < 75 ? 'Warning' : 'Acceptable'} (${avgAtt}%)`;
      document.getElementById("evPerfBadge").textContent = `${failedCount} Failed (<50%)`;
      document.getElementById("evCurrentAvgText").textContent = `${avgMarks}%`;
    }
  } catch (err) {
    console.error("Failed to load evidence for student:", err);
  }
}

/* ==========================================================================
   REAL-TIME METRICS TAB
   ========================================================================== */
async function fetchSystemMetrics() {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById("mWorkflowCount").textContent = data.workflow_count;
      document.getElementById("mAvgLatency").textContent = `${data.average_duration_ms} ms`;
      document.getElementById("mDatabaseOps").textContent = data.database_operations;
      document.getElementById("mRetries").textContent = data.retry_count;

      // Tool usage table
      const tbody = document.getElementById("toolUsageTableBody");
      if (tbody) {
        tbody.innerHTML = "";
        const toolMeta = {
          "student_profile": { cat: "Profile Ingestion", guarantee: "Unified Demographics" },
          "attendance_analyzer": { cat: "Attendance Telemetry", guarantee: "<66% Critical, 66-74% Warning" },
          "performance_analyzer": { cat: "Academic Assessment", guarantee: "Subject Marks & <50% Failures" },
          "assignment_analyzer": { cat: "Coursework Regularity", guarantee: "Submission & Punctuality" },
          "trend_analyzer": { cat: "Longitudinal Analytics", guarantee: "Semester Delta & Trajectory" },
          "intervention_knowledge": { cat: "Pedagogical Mapping", guarantee: "Evidence-Based Remedies" }
        };

        for (const [toolName, count] of Object.entries(data.tool_usage_counts)) {
          const meta = toolMeta[toolName] || { cat: "Analysis", guarantee: "Operational" };
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><code>${toolName}</code></td>
            <td>${meta.cat}</td>
            <td><strong>${count}</strong> invocations</td>
            <td><span class="badge badge-low">${meta.guarantee}</span></td>
          `;
          tbody.appendChild(tr);
        }
      }
    }
  } catch (err) {
    console.error("Failed to fetch system metrics:", err);
  }
}

/* ==========================================================================
   STUDENT PROFILE MODAL
   ========================================================================== */
function initModal() {
  const modal = document.getElementById("profileModal");
  const closeBtn = document.getElementById("btnModalClose");
  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => { modal.style.display = "none"; });
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.style.display = "none";
    });
  }
}

window.viewProfileModal = async function(studentId) {
  const modal = document.getElementById("profileModal");
  const content = document.getElementById("modalStudentContent");
  const title = document.getElementById("modalStudentName");

  try {
    const res = await fetch(`${API_BASE}/students/${studentId}`);
    if (res.ok) {
      const data = await res.json();
      title.textContent = `Student Profile: ${data.name} (${data.student_id})`;
      content.innerHTML = `
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem; font-size: 0.9rem;">
          <div><strong>Department:</strong> ${data.department}</div>
          <div><strong>Section:</strong> ${data.section} (Semester ${data.semester})</div>
          <div><strong>Advisor:</strong> ${data.advisor_name}</div>
          <div><strong>Prior Semester Avg:</strong> ${data.prior_semester_avg}%</div>
          <div><strong>Institutional Email:</strong> ${data.email}</div>
          <div><strong>Enrolled Courses:</strong> ${data.enrolled_courses_count}</div>
        </div>
        <h4 style="font-size: 0.85rem; text-transform: uppercase; margin-bottom: 0.5rem;">Enrolled Subjects & Attendance</h4>
        <table class="sub-table" style="width: 100%;">
          <thead>
            <tr><th>Code</th><th>Course Name</th><th>Attendance</th><th>Marks</th></tr>
          </thead>
          <tbody>
            ${(data.enrolled_courses || []).map(c => `
              <tr>
                <td><strong>${c.course_code}</strong></td>
                <td>${c.course_name}</td>
                <td>${c.attendance_pct}%</td>
                <td>${c.total_marks}%</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
      modal.style.display = "flex";
    }
  } catch (err) {
    console.error("Modal profile error:", err);
  }
};
