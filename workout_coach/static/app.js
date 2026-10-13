/**
 * APEX AI Workout Coach — Interactive Frontend Client
 * UI/UX Pro Max Architecture with Cloud Firestore & Athlete Management
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const userSelectDropdown = document.getElementById("userSelectDropdown");
  const headerAvatar = document.getElementById("headerAvatar");
  const adapterName = document.getElementById("adapterName");

  // Hero Banner Elements
  const heroGoalBadge = document.getElementById("heroGoalBadge");
  const heroLevelBadge = document.getElementById("heroLevelBadge");
  const heroSplitBadge = document.getElementById("heroSplitBadge");
  const heroSafetyBadge = document.getElementById("heroSafetyBadge");
  const heroSafetyText = document.getElementById("heroSafetyText");

  // Create User Modal Elements
  const createUserModal = document.getElementById("createUserModal");
  const btnOpenCreateUserModal = document.getElementById("btnOpenCreateUserModal");
  const btnCloseCreateUserModal = document.getElementById("btnCloseCreateUserModal");
  const btnCancelCreateUser = document.getElementById("btnCancelCreateUser");
  const createUserForm = document.getElementById("createUserForm");

  // Chat Elements
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatMessages = document.getElementById("chatMessages");
  const coachChatDrawer = document.getElementById("coachChatDrawer");
  const btnToggleCoachDrawer = document.getElementById("btnToggleCoachDrawer");

  // State
  let currentUserId = "athlete_alex";
  let athletesList = [];
  let exerciseCatalog = [];
  let loggedExercises = [];

  // ==========================================================================
  // TOAST NOTIFICATION SYSTEM
  // ==========================================================================
  function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconSvg = '';
    if (type === 'success') {
      iconSvg = '<svg class="icon-xs" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    } else if (type === 'error') {
      iconSvg = '<svg class="icon-xs" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    } else {
      iconSvg = '<svg class="icon-xs" viewBox="0 0 24 24" fill="none" stroke="#F97316" stroke-width="3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
    }

    toast.innerHTML = `${iconSvg} <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "all 200ms ease";
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }

  // ==========================================================================
  // TAB NAVIGATION
  // ==========================================================================
  const tabBtns = document.querySelectorAll(".segment-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  function switchTab(tabId) {
    tabBtns.forEach(b => {
      const isTarget = b.dataset.tab === tabId;
      b.classList.toggle("active", isTarget);
      b.setAttribute("aria-selected", isTarget ? "true" : "false");
    });
    tabPanes.forEach(pane => {
      pane.classList.toggle("active", pane.id === tabId);
    });

    if (tabId === "tab-plan") loadActivePlan();
    if (tabId === "tab-progress") loadProgress();
    if (tabId === "tab-profile") loadProfile();
    if (tabId === "tab-maps") scoutFacilities();
  }

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Hero Quick Actions
  document.getElementById("btnHeroGeneratePlan")?.addEventListener("click", () => {
    switchTab("tab-plan");
    generatePlan();
  });
  document.getElementById("btnHeroQuickLog")?.addEventListener("click", () => {
    switchTab("tab-log");
  });

  // ==========================================================================
  // BACKEND HEALTH & METADATA
  // ==========================================================================
  async function checkHealth() {
    try {
      const res = await fetch("/api/v1/health");
      const data = await res.json();
      const storage = (data.storage_backend || "").includes("Firestore") ? "Cloud Firestore" : "SQLite";
      const model = (data.model_adapter || "").replace("ModelAdapter", "");
      adapterName.textContent = `${storage} • ${model}`;
    } catch (err) {
      adapterName.textContent = "Offline";
    }
  }

  // ==========================================================================
  // USER / ATHLETE MANAGEMENT & SWITCHER
  // ==========================================================================
  async function fetchAthletes() {
    try {
      const res = await fetch("/api/v1/profiles");
      if (res.ok) {
        const raw = await res.json();
        athletesList = (raw || []).filter(ath => {
          const id = (ath.user_id || "").toLowerCase();
          return !id.startsWith("test_") && !id.startsWith("api_test_") && !id.startsWith("cloud_user_") && !id.startsWith("tmp_");
        });
      }
    } catch (e) {
      console.warn("Could not fetch athletes list:", e);
    }

    // Default list if empty
    if (!athletesList || athletesList.length === 0) {
      athletesList = [
        { user_id: "athlete_alex", fitness_goal: "strength", experience_level: "intermediate", days_per_week: 3, limitations: [] }
      ];
    }

    renderAthleteDropdown();
  }

  function renderAthleteDropdown() {
    userSelectDropdown.innerHTML = "";
    if (athletesList.length > 0 && !athletesList.some(ath => ath.user_id === currentUserId)) {
      currentUserId = athletesList[0].user_id;
    }
    athletesList.forEach(ath => {
      const opt = document.createElement("option");
      opt.value = ath.user_id;
      // Capitalize / format name
      const displayName = ath.user_id.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
      opt.textContent = `${displayName} (${ath.fitness_goal})`;
      if (ath.user_id === currentUserId) opt.selected = true;
      userSelectDropdown.appendChild(opt);
    });

    // Update avatar
    const activeName = currentUserId.replace(/^athlete_/, "");
    headerAvatar.textContent = (activeName[0] || "A").toUpperCase();
  }

  userSelectDropdown.addEventListener("change", (e) => {
    currentUserId = e.target.value;
    const activeName = currentUserId.replace(/^athlete_/, "");
    headerAvatar.textContent = (activeName[0] || "A").toUpperCase();
    showToast(`Switched active athlete to: ${currentUserId}`, "info");
    
    loadProfile();
    loadActivePlan();
    loadProgress();
  });

  // ==========================================================================
  // CREATE USER MODAL FLOW
  // ==========================================================================
  function openCreateUserModal() {
    createUserModal.classList.add("active");
    document.getElementById("newUserId").value = "";
    document.getElementById("newUserId").focus();
  }

  function closeCreateUserModal() {
    createUserModal.classList.remove("active");
  }

  btnOpenCreateUserModal?.addEventListener("click", openCreateUserModal);
  btnCloseCreateUserModal?.addEventListener("click", closeCreateUserModal);
  btnCancelCreateUser?.addEventListener("click", closeCreateUserModal);

  // Close on outside click
  createUserModal?.addEventListener("click", (e) => {
    if (e.target === createUserModal) closeCreateUserModal();
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && createUserModal.classList.contains("active")) {
      closeCreateUserModal();
    }
  });

  // Submit New User
  createUserForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btnSubmit = document.getElementById("btnConfirmCreateUser");
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Creating in Firestore...";

    const rawId = document.getElementById("newUserId").value.trim().toLowerCase().replace(/\s+/g, "_");
    const goal = document.querySelector("input[name='newGoal']:checked")?.value || "strength";
    const level = document.getElementById("newLevel").value;
    const days = parseInt(document.getElementById("newDays").value) || 3;

    const equip = Array.from(document.querySelectorAll("input[name='newEquipment']:checked")).map(cb => cb.value);
    const limits = Array.from(document.querySelectorAll("input[name='newLimitations']:checked")).map(cb => cb.value);

    const newProfile = {
      user_id: rawId,
      fitness_goal: goal,
      experience_level: level,
      days_per_week: days,
      session_duration_minutes: 45,
      available_equipment: equip.length ? equip : ["bodyweight"],
      limitations: limits,
      preferences: []
    };

    try {
      // 1. Save Profile
      const saveRes = await fetch("/api/v1/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newProfile)
      });

      if (!saveRes.ok) throw new Error("Failed to save profile to database");

      // 2. Set Active User
      currentUserId = rawId;
      await fetchAthletes();
      closeCreateUserModal();
      showToast(`🎉 Athlete '${rawId}' created in Cloud Firestore!`, "success");

      // 3. Automatically Generate Customized Workout Plan
      await generatePlan();

      // 4. Welcome Coach Message
      appendChatMessage("coach", `Welcome **${rawId}**! I have calibrated your training profile in Cloud Firestore with goal **${goal.toUpperCase()}** and **${days} days/week**. Your customized, injury-safe routine is ready in the Active Routine tab!`);

      // Refresh all tabs
      loadProfile();
      loadProgress();
    } catch (err) {
      showToast(`Error creating user: ${err.message}`, "error");
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-sm"><polyline points="20 6 9 17 4 12"></polyline></svg> Create Athlete & Generate Routine`;
    }
  });

  // ==========================================================================
  // EXERCISE CATALOG
  // ==========================================================================
  async function loadExerciseCatalog() {
    try {
      const res = await fetch("/api/v1/exercises");
      const data = await res.json();
      exerciseCatalog = data.exercises || [];
    } catch (e) {
      console.error("Failed to load exercise catalog", e);
    }
  }

  // ==========================================================================
  // TAB 1: WORKOUT PLAN
  // ==========================================================================
  async function loadActivePlan() {
    const title = document.getElementById("planTitle");
    const meta = document.getElementById("planMeta");
    const rationaleBox = document.getElementById("planRationaleBox");
    const rationaleText = document.getElementById("planRationaleText");
    const container = document.getElementById("planSessionsContainer");

    try {
      const res = await fetch(`/api/v1/workout-plans/${currentUserId}/current`);
      if (res.status === 404) {
        title.textContent = "No Active Plan";
        meta.textContent = "Generate a customized routine to get started.";
        rationaleBox.style.display = "none";
        container.innerHTML = `
          <div class="empty-state-card">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="icon-xl">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
            </div>
            <h3>No Routine Generated Yet</h3>
            <p>Click "Generate Custom Plan" to create a balanced, safe routine for ${currentUserId}.</p>
          </div>
        `;
        return;
      }

      const plan = await res.json();
      title.textContent = plan.plan_name;
      const formattedSplit = plan.split_type.replace(/_/g, " ").toUpperCase();
      meta.textContent = `${formattedSplit} • ${plan.days_per_week} Days/Week • Goal: ${plan.goal.toUpperCase()}`;
      
      if (plan.rationale) {
        rationaleText.innerHTML = `<strong>Coach Biomechanical Rationale:</strong> ${plan.rationale}`;
        rationaleBox.style.display = "flex";
      } else {
        rationaleBox.style.display = "none";
      }

      // Update Hero Banner
      heroGoalBadge.textContent = plan.goal.replace(/_/g, " ").toUpperCase();
      heroSplitBadge.textContent = `${plan.days_per_week} Days / Week`;

      // Render Days
      container.innerHTML = "";
      plan.sessions.forEach((sess, idx) => {
        const card = document.createElement("div");
        card.className = "plan-day-card";

        let exRowsHtml = "";
        sess.exercises.forEach(e => {
          exRowsHtml += `
            <tr>
              <td>
                <span class="plan-exercise-name">${e.exercise_name}</span>
                <span class="plan-exercise-tag">${e.movement_pattern || 'Compound'}</span>
              </td>
              <td><span class="plan-target-badge">${e.target_sets} sets × ${e.target_reps}</span></td>
              <td><span class="plan-rest-badge">${e.rest_seconds}s rest</span></td>
              <td>
                <svg viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5" class="icon-xs" title="Safety Verified">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </td>
            </tr>
          `;
        });

        const dayTitle = sess.day_name || (sess.session_name ? `Day ${sess.day_number}: ${sess.session_name}` : `Day ${sess.day_number || 1}`);

        card.innerHTML = `
          <div class="plan-day-header">
            <div>
              <div class="plan-day-title">${dayTitle}</div>
              <div class="plan-day-focus">Target Focus: ${sess.focus || 'Full Body'} • ${sess.exercises.length} Movements</div>
            </div>
          </div>
          <table class="plan-exercise-table">
            <thead>
              <tr>
                <th>Exercise</th>
                <th>Target Volume</th>
                <th>Rest</th>
                <th>Safety</th>
              </tr>
            </thead>
            <tbody>
              ${exRowsHtml}
            </tbody>
          </table>
        `;
        container.appendChild(card);
      });

    } catch (e) {
      console.error("Failed to load active plan", e);
    }
  }

  async function generatePlan() {
    const btn = document.getElementById("btnGeneratePlan");
    const origHtml = btn.innerHTML;
    btn.disabled = true;
    btn.textContent = "Synthesizing Plan...";

    try {
      const res = await fetch("/api/v1/workout-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: currentUserId })
      });
      if (!res.ok) throw new Error("Plan generation failed");
      const plan = await res.json();
      showToast(`⚡ Generated '${plan.plan_name}' successfully!`, "success");
      await loadActivePlan();
    } catch (err) {
      showToast(`Error: ${err.message}`, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = origHtml;
    }
  }

  document.getElementById("btnGeneratePlan")?.addEventListener("click", generatePlan);

  // ==========================================================================
  // TAB 2: WORKOUT LOGGER
  // ==========================================================================
  // Date default to today
  const logDateInput = document.getElementById("logDate");
  if (logDateInput) {
    logDateInput.value = new Date().toISOString().split("T")[0];
  }

  // RPE Slider label
  const rpeSlider = document.getElementById("logRpe");
  const rpeDisplay = document.getElementById("rpeDisplayVal");
  const rpeDescriptions = {
    1: "Very Light Effort",
    2: "Light Warmup",
    3: "Moderate Warmup",
    4: "Moderate Work",
    5: "Noticeable Effort",
    6: "Moderate-Hard (4 reps reserve)",
    7: "Hard (3 reps in reserve)",
    8: "Challenging (2 reps reserve)",
    9: "Extremely Hard (1 rep reserve)",
    10: "Maximum Effort (0 reserve)"
  };

  rpeSlider?.addEventListener("input", (e) => {
    const val = e.target.value;
    rpeDisplay.textContent = `RPE ${val} • ${rpeDescriptions[val] || ''}`;
  });

  function addExerciseToLogUi(defaultExerciseId = "ex_dumbbell_bench_press") {
    const container = document.getElementById("loggedExercisesList");
    const exDiv = document.createElement("div");
    exDiv.className = "exercise-log-card";

    let selectOptions = "";
    exerciseCatalog.forEach(ex => {
      const selected = ex.id === defaultExerciseId ? "selected" : "";
      selectOptions += `<option value="${ex.id}" ${selected}>${ex.name} (${ex.category})</option>`;
    });

    exDiv.innerHTML = `
      <div class="exercise-log-header">
        <select class="select-control exercise-id-select" style="max-width: 300px;">
          ${selectOptions}
        </select>
        <button type="button" class="btn btn-outline btn-sm btn-remove-ex" style="color:#EF4444;">✕ Remove</button>
      </div>
      <table class="sets-table">
        <thead>
          <tr>
            <th>Set #</th>
            <th>Weight (kg)</th>
            <th>Reps</th>
            <th>RPE</th>
          </tr>
        </thead>
        <tbody class="sets-body">
          <tr>
            <td><strong>1</strong></td>
            <td><input type="number" step="0.5" class="set-weight" value="20.0" required></td>
            <td><input type="number" class="set-reps" value="10" required></td>
            <td><input type="number" step="0.5" class="set-rpe" value="7.0" min="1" max="10"></td>
          </tr>
          <tr>
            <td><strong>2</strong></td>
            <td><input type="number" step="0.5" class="set-weight" value="22.5" required></td>
            <td><input type="number" class="set-reps" value="10" required></td>
            <td><input type="number" step="0.5" class="set-rpe" value="8.0" min="1" max="10"></td>
          </tr>
          <tr>
            <td><strong>3</strong></td>
            <td><input type="number" step="0.5" class="set-weight" value="22.5" required></td>
            <td><input type="number" class="set-reps" value="8" required></td>
            <td><input type="number" step="0.5" class="set-rpe" value="8.5" min="1" max="10"></td>
          </tr>
        </tbody>
      </table>
    `;

    exDiv.querySelector(".btn-remove-ex").addEventListener("click", () => exDiv.remove());
    container.appendChild(exDiv);
  }

  document.getElementById("btnAddExerciseToLog")?.addEventListener("click", () => {
    addExerciseToLogUi();
  });

  // Log Form Submission
  document.getElementById("logWorkoutForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btnSubmit = document.getElementById("btnSubmitLog");
    const statusMsg = document.getElementById("logStatusMsg");
    btnSubmit.disabled = true;
    statusMsg.className = "inline-status-msg";
    statusMsg.textContent = "Writing telemetry to Cloud Firestore...";

    const performedExercises = [];
    const exCards = document.querySelectorAll(".exercise-log-card");

    exCards.forEach(card => {
      const exSelect = card.querySelector(".exercise-id-select");
      const exId = exSelect.value;
      const exName = exSelect.options[exSelect.selectedIndex].text.split(" (")[0];

      const sets = [];
      const setRows = card.querySelectorAll(".sets-body tr");
      setRows.forEach((row, sIdx) => {
        const weight = parseFloat(row.querySelector(".set-weight").value) || 0;
        const reps = parseInt(row.querySelector(".set-reps").value) || 0;
        const rpe = parseFloat(row.querySelector(".set-rpe").value) || 7.0;
        sets.push({
          set_number: sIdx + 1,
          weight_kg: weight,
          reps: reps,
          reps_performed: reps,
          rpe: rpe,
          completed: true,
          is_completed: true
        });
      });

      performedExercises.push({
        exercise_id: exId,
        exercise_name: exName,
        sets: sets,
        skipped: false
      });
    });

    const dateVal = document.getElementById("logDate").value || new Date().toISOString().split("T")[0];
    const durationVal = parseInt(document.getElementById("logDuration").value) || 45;
    const rpeVal = parseFloat(rpeSlider.value) || 7.0;
    const feedbackVal = document.getElementById("logFeedback").value || "";
    const generatedId = `sess_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

    const payload = {
      id: generatedId,
      user_id: currentUserId,
      session_name: "Completed Workout",
      session_date: dateVal,
      started_at: dateVal,
      duration_minutes: durationVal,
      perceived_effort_rpe: rpeVal,
      rpe_session: rpeVal,
      feedback: feedbackVal,
      feedback_notes: feedbackVal,
      exercises: performedExercises
    };

    try {
      const res = await fetch("/api/v1/workout-sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        let errDetail = "Failed to record workout session";
        try {
          const errData = await res.json();
          if (errData.detail) {
            errDetail = typeof errData.detail === "string"
              ? errData.detail
              : Array.isArray(errData.detail)
                ? errData.detail.map(d => `${(d.loc || []).join(".")}: ${d.msg}`).join("; ")
                : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        throw new Error(errDetail);
      }

      const session = await res.json();
      const volText = (session.total_volume_kg !== undefined && session.total_volume_kg !== null)
        ? `${session.total_volume_kg} kg`
        : "recorded";

      showToast(`💾 Session recorded to Cloud Firestore! Volume: ${volText}`, "success");
      statusMsg.className = "inline-status-msg success";
      statusMsg.textContent = `✅ Saved session (${volText} volume)`;

      // Refresh progress & active plans, then switch tabs
      loadProgress();
      loadActivePlan();

      setTimeout(() => {
        switchTab("tab-progress");
        statusMsg.textContent = "";
      }, 1000);

    } catch (err) {
      statusMsg.className = "inline-status-msg error";
      statusMsg.textContent = `❌ Error: ${err.message}`;
      showToast(err.message, "error");
    } finally {
      btnSubmit.disabled = false;
    }
  });

  // ==========================================================================
  // TAB 3: PROGRESS & TELEMETRY
  // ==========================================================================
  async function loadProgress() {
    try {
      const res = await fetch(`/api/v1/progress/${currentUserId}`);
      if (!res.ok) return;

      const data = await res.json();

      // Update KPI with safe fallbacks
      const totalSessions = data.total_completed_sessions ?? data.total_sessions_completed ?? 0;
      let adherence = 0;
      if (data.adherence_rate_14d !== undefined && data.adherence_rate_14d !== null) {
        adherence = Math.round(data.adherence_rate_14d);
      } else if (data.weekly_adherence_rate !== undefined && data.weekly_adherence_rate !== null) {
        adherence = Math.round(data.weekly_adherence_rate * 100);
      }
      const totalVol = data.total_volume_kg ?? 0;

      document.getElementById("statSessions").textContent = totalSessions;
      document.getElementById("statAdherence").textContent = `${adherence}%`;
      document.getElementById("statVolume").textContent = `${Number(totalVol).toLocaleString()} kg`;

      // Overload Guidance
      const adjList = document.getElementById("adjustmentsList");
      const recs = data.progression_recommendations || data.recommended_adjustments || [];
      if (recs && recs.length > 0) {
        let itemsHtml = "<ul>";
        recs.forEach(r => {
          if (typeof r === "string") {
            itemsHtml += `<li>${r}</li>`;
          } else {
            itemsHtml += `<li><strong>${r.exercise_name || 'Exercise'}:</strong> ${r.recommendation || ''} <em>(${r.rationale || 'Telemetry-driven'})</em></li>`;
          }
        });
        itemsHtml += "</ul>";
        adjList.innerHTML = itemsHtml;
      } else {
        adjList.innerHTML = `<p class="empty-hint">Accumulating workout logs to compute deterministic progressive overload.</p>`;
      }

      // Trends Table
      const trendsBody = document.getElementById("exerciseTrendsBody");
      trendsBody.innerHTML = "";
      const trends = data.exercise_records || data.exercise_trends || {};
      const exKeys = Object.keys(trends);

      if (exKeys.length === 0) {
        trendsBody.innerHTML = `<tr><td colspan="6" class="text-muted text-center py-4">No completed exercise logs recorded yet.</td></tr>`;
        return;
      }

      exKeys.forEach(name => {
        const t = trends[name];
        const row = document.createElement("tr");
        const maxW = t.max_weight_kg ?? 0;
        const e1rm = t.estimated_1rm_kg ?? 0;
        const exVol = t.total_volume_kg ?? 0;
        const displayName = t.exercise_name || name;
        row.innerHTML = `
          <td><strong>${displayName}</strong></td>
          <td>${t.sessions_logged ?? 1}</td>
          <td><span class="metric-highlight">${maxW} kg</span></td>
          <td><span class="metric-highlight">${e1rm} kg</span></td>
          <td>${Number(exVol).toLocaleString()} kg</td>
          <td>
            <span class="pill pill-guard">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="icon-xs">
                <polyline points="18 15 12 9 6 15"></polyline>
              </svg>
              ${t.trend || 'stable'}
            </span>
          </td>
        `;
        trendsBody.appendChild(row);
      });

    } catch (e) {
      console.error("Failed to load progress telemetry", e);
    }
  }

  document.getElementById("btnRefreshProgress")?.addEventListener("click", () => {
    loadProgress();
    showToast("Telemetry synced from Cloud Firestore", "info");
  });

  // ==========================================================================
  // TAB 4: PROFILE & SAFETY BOUNDARIES
  // ==========================================================================
  async function loadProfile() {
    try {
      const res = await fetch(`/api/v1/profiles/${currentUserId}`);
      if (!res.ok) return;

      const p = await res.json();
      document.getElementById("profileGoal").value = p.fitness_goal;
      document.getElementById("profileLevel").value = p.experience_level;
      document.getElementById("profileDays").value = p.days_per_week;

      // Update hero banner
      heroGoalBadge.textContent = p.fitness_goal.replace(/_/g, " ").toUpperCase();
      heroLevelBadge.textContent = p.experience_level.toUpperCase();
      heroSplitBadge.textContent = `${p.days_per_week} Days / Week`;

      if (p.limitations && p.limitations.length > 0) {
        heroSafetyText.textContent = `Shield: ${p.limitations.length} Contraindications Protected`;
        heroSafetyBadge.style.color = "#F87171";
        heroSafetyBadge.style.borderColor = "rgba(239, 68, 68, 0.4)";
      } else {
        heroSafetyText.textContent = "Full Biomechanical Mobility";
        heroSafetyBadge.style.color = "#34D399";
        heroSafetyBadge.style.borderColor = "rgba(16, 185, 129, 0.3)";
      }

      // Checkboxes
      document.querySelectorAll("input[name='equipment']").forEach(cb => {
        cb.checked = (p.available_equipment || []).includes(cb.value);
      });
      document.querySelectorAll("input[name='limitations']").forEach(cb => {
        cb.checked = (p.limitations || []).includes(cb.value);
      });
    } catch (e) {
      console.warn("No existing profile for", currentUserId);
    }
  }

  document.getElementById("profileForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const statusMsg = document.getElementById("profileStatusMsg");
    statusMsg.className = "inline-status-msg";
    statusMsg.textContent = "Updating profile in Cloud Firestore...";

    const equip = Array.from(document.querySelectorAll("input[name='equipment']:checked")).map(cb => cb.value);
    const limits = Array.from(document.querySelectorAll("input[name='limitations']:checked")).map(cb => cb.value);

    const payload = {
      user_id: currentUserId,
      fitness_goal: document.getElementById("profileGoal").value,
      experience_level: document.getElementById("profileLevel").value,
      days_per_week: parseInt(document.getElementById("profileDays").value) || 3,
      session_duration_minutes: 45,
      available_equipment: equip,
      limitations: limits,
      preferences: []
    };

    try {
      const res = await fetch("/api/v1/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        statusMsg.className = "inline-status-msg success";
        statusMsg.textContent = "✅ Profile updated in Cloud Firestore!";
        showToast("Profile updated successfully", "success");
        loadProfile();
        setTimeout(() => { statusMsg.textContent = ""; }, 3000);
      } else {
        statusMsg.className = "inline-status-msg error";
        statusMsg.textContent = "❌ Failed to save profile.";
      }
    } catch (err) {
      statusMsg.className = "inline-status-msg error";
      statusMsg.textContent = `❌ Error: ${err.message}`;
    }
  });

  // ==========================================================================
  // TAB 5: GOOGLE MAPS & GYMS EXPLORER
  // ==========================================================================
  const mapsLocationInput = document.getElementById("mapsLocationInput");
  const mapsFacilityType = document.getElementById("mapsFacilityType");
  const btnScoutFacilities = document.getElementById("btnScoutFacilities");
  const mapsVenuesContainer = document.getElementById("mapsVenuesContainer");

  function renderVenueCards(venues, targetContainer, source) {
    if (!targetContainer) return;
    targetContainer.innerHTML = "";

    if (!venues || venues.length === 0) {
      targetContainer.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 2rem;">
          No facilities found for this query. Try a broader city or different category.
        </div>
      `;
      return;
    }

    const isLive = source === "google_places_api_new";
    const sourceBadge = isLive
      ? `<span class="pill" style="background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 0.72rem; padding: 2px 8px; border-radius: 9999px;">Verified Live Google Places</span>`
      : `<span class="pill" style="background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 0.72rem; padding: 2px 8px; border-radius: 9999px;">⚠️ Sample Demonstration Data (Simulated Fallback)</span>`;

    venues.forEach((v, idx) => {
      const card = document.createElement("div");
      card.className = "venue-card";

      const stars = "★".repeat(Math.round(v.rating || 4.5)) + "☆".repeat(Math.max(0, 5 - Math.round(v.rating || 4.5)));
      const iframeId = `map_iframe_${idx}_${Date.now()}`;
      const revCount = v.reviews || v.user_ratings_total || 45;

      card.innerHTML = `
        <div>
          <div class="venue-card-header" style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem; flex-wrap:wrap;">
            <h3 class="venue-title" style="margin:0;">${v.name}</h3>
            <div style="display:flex; gap:0.35rem; align-items:center; flex-wrap:wrap;">
              <span class="venue-category-badge">${v.category || "Fitness"}</span>
              ${sourceBadge}
            </div>
          </div>
          <div class="venue-rating-row" style="margin-top: 0.35rem;">
            <span>${stars}</span>
            <strong>${v.rating || "4.8"}</strong>
            <span class="venue-rating-count">(${revCount}+ reviews)</span>
          </div>
          <p class="venue-address" style="margin-top: 0.5rem;">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-xs" style="flex-shrink: 0; margin-top: 2px;">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            <span>${v.formatted_address || v.address}</span>
          </p>
          ${v.highlight ? `<p class="venue-highlight" style="margin-top: 0.4rem;">${v.highlight}</p>` : ''}
        </div>

        <div>
          <div class="venue-actions-row">
            <a href="${v.google_maps_url}" target="_blank" rel="noopener noreferrer" class="btn-maps-action btn-maps-view" title="Open Google Maps search">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-xs">
                <circle cx="12" cy="12" r="10"></circle>
                <polygon points="12 8 8 12 12 16 12 8"></polygon>
              </svg>
              <span>Google Maps</span>
            </a>
            <a href="${v.directions_url}" target="_blank" rel="noopener noreferrer" class="btn-maps-action btn-maps-dir" title="Get direct navigation route">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-xs">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
              <span>Directions</span>
            </a>
            <button type="button" class="btn-maps-action btn-maps-toggle-preview" data-iframe-id="${iframeId}" data-embed-url="${v.embed_url || ''}">
              <span>Map Preview</span>
            </button>
          </div>

          <div class="venue-map-iframe-container" id="${iframeId}">
            <iframe class="venue-map-iframe" src="${v.embed_url || v.google_maps_url + '&output=embed'}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
          </div>
        </div>
      `;

      targetContainer.appendChild(card);
    });

    // Wire up preview toggles
    targetContainer.querySelectorAll(".btn-maps-toggle-preview").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.iframeId;
        const container = document.getElementById(id);
        if (container) {
          const isVis = container.classList.toggle("visible");
          btn.textContent = isVis ? "Hide Map" : "Map Preview";
        }
      });
    });
  }

  async function scoutFacilities(optLocation, optType) {
    const loc = optLocation || (mapsLocationInput ? mapsLocationInput.value : "Downtown") || "Downtown";
    const fType = optType || (mapsFacilityType ? mapsFacilityType.value : "gym") || "gym";

    if (mapsVenuesContainer) {
      mapsVenuesContainer.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 2rem;">
          <span class="status-dot pulsating" style="display:inline-block; margin-right: 0.5rem;"></span>
          Scouting top-rated ${fType} facilities near ${loc} on Google Maps...
        </div>
      `;
    }

    try {
      const res = await fetch(`/api/v1/maps/facilities?location=${encodeURIComponent(loc)}&facility_type=${encodeURIComponent(fType)}`);
      const data = await res.json();
      if (data && data.venues) {
        renderVenueCards(data.venues, mapsVenuesContainer, data.source);
      }
    } catch (err) {
      if (mapsVenuesContainer) {
        mapsVenuesContainer.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; color: #EF4444; padding: 2rem;">
            Failed to load venues: ${err.message}
          </div>
        `;
      }
    }
  }

  btnScoutFacilities?.addEventListener("click", () => {
    scoutFacilities();
  });

  document.querySelectorAll(".location-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      if (mapsLocationInput) mapsLocationInput.value = chip.dataset.loc;
      scoutFacilities(chip.dataset.loc);
    });
  });

  // ==========================================================================
  // A2UI PROTOCOL (v0.8) MINI-RENDERER
  // ==========================================================================
  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function boundStr(v) {
    if (v == null) return "";
    if (typeof v === "string") return v;
    if (typeof v.literalString === "string") return v.literalString;
    return "";
  }

  function childIds(props) {
    const ids = [];
    if (props && typeof props.child === "string") ids.push(props.child);
    const ch = props && props.children;
    if (ch && Array.isArray(ch.explicitList)) {
      for (const c of ch.explicitList) {
        if (typeof c === "string") ids.push(c);
      }
    }
    return ids;
  }

  function buildA2UINode(id, comps, seen) {
    if (!id || seen.has(id)) return null;
    seen.add(id);
    const spec = comps[id];
    if (!spec || typeof spec !== "object") return null;
    const type = Object.keys(spec)[0];
    const props = spec[type] || {};
    const kids = () => childIds(props).map(cid => buildA2UINode(cid, comps, seen)).filter(Boolean);

    switch (type) {
      case "Card": {
        const d = el("div", "a2card");
        kids().forEach(n => d.appendChild(n));
        return d;
      }
      case "Column":
      case "List": {
        const horizontal = type === "List" && props.direction === "horizontal";
        const d = el("div", horizontal ? "a2row" : "a2col");
        kids().forEach(n => d.appendChild(n));
        return d;
      }
      case "Row": {
        const d = el("div", "a2row" + (props.distribution === "spaceBetween" ? " between" : ""));
        kids().forEach(n => d.appendChild(n));
        return d;
      }
      case "Text": {
        const t = el("div", "a2text");
        const hint = String(props.usageHint || "body").toLowerCase();
        if (["h1", "h2", "h3", "h4", "h5", "h6"].includes(hint)) t.classList.add("a2-" + hint);
        else if (hint === "caption") t.classList.add("a2-caption");
        t.textContent = boundStr(props.text);
        return t;
      }
      case "Divider":
        return el("hr", "a2divider");
      case "Image": {
        const src = boundStr(props.url || props.src);
        if (!/^https?:\/\//i.test(src)) return null;
        const img = el("img", "a2img");
        img.src = src;
        img.alt = boundStr(props.alt) || "";
        return img;
      }
      default:
        return null;
    }
  }

  function renderA2UISurface(messages, container) {
    if (!Array.isArray(messages) || messages.length === 0) return false;
    const comps = {};
    const roots = [];

    for (const m of messages) {
      if (m.beginRendering && typeof m.beginRendering.root === "string") {
        roots.push(m.beginRendering.root);
      }
      const su = m.surfaceUpdate;
      if (su && Array.isArray(su.components)) {
        for (const c of su.components) {
          if (c && c.id && c.component) comps[c.id] = c.component;
        }
      }
    }

    let rootIds = roots.filter(r => comps[r]);
    if (rootIds.length === 0) {
      const referenced = new Set();
      for (const id in comps) {
        const spec = comps[id];
        childIds(spec[Object.keys(spec)[0]] || {}).forEach(c => referenced.add(c));
      }
      rootIds = Object.keys(comps).filter(id => !referenced.has(id));
    }

    let drew = false;
    for (const rid of rootIds) {
      const node = buildA2UINode(rid, comps, new Set());
      if (node) {
        container.appendChild(node);
        drew = true;
      }
    }
    return drew;
  }

  // ==========================================================================
  // RONNY COACH CONVERSATIONAL DRAWER
  // ==========================================================================
  function appendChatMessage(role, text, toolBadges = [], isSafety = false, a2uiMessages = null, mapsData = null) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-msg ${role} ${isSafety ? 'safety-alert' : ''}`;

    let toolsHtml = "";
    if (toolBadges && toolBadges.length > 0) {
      toolsHtml = toolBadges.map(t => `
        <div style="font-size:0.7rem; color:#F97316; margin-top:0.3rem;">
          ⚙️ Executed tool: <strong>${t.tool}</strong>
        </div>
      `).join("");
    }

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.innerHTML = text ? text.replace(/\n/g, "<br>") : "";

    // Render A2UI cards if provided
    if (a2uiMessages && Array.isArray(a2uiMessages) && a2uiMessages.length > 0) {
      const a2uiContainer = document.createElement("div");
      a2uiContainer.className = "a2ui-embed-wrapper";
      const rendered = renderA2UISurface(a2uiMessages, a2uiContainer);
      if (rendered) {
        bubble.appendChild(a2uiContainer);
      }
    }

    // Render Google Maps venue cards if present
    if (mapsData && Array.isArray(mapsData.venues) && mapsData.venues.length > 0) {
      const mapsWrapper = document.createElement("div");
      mapsWrapper.style.marginTop = "0.75rem";
      const isLive = mapsData.source === "google_places_api_new";
      const badge = isLive
        ? `<span style="font-size:0.65rem; background:rgba(16,185,129,0.15); color:#10B981; padding:1px 6px; border-radius:9999px; border:1px solid rgba(16,185,129,0.3);">Google Places</span>`
        : `<span style="font-size:0.65rem; background:rgba(245,158,11,0.15); color:#F59E0B; padding:1px 6px; border-radius:9999px; border:1px solid rgba(245,158,11,0.3);">Demonstration Data</span>`;

      mapsData.venues.slice(0, 3).forEach(v => {
        const miniCard = document.createElement("div");
        miniCard.className = "chat-maps-card";
        miniCard.innerHTML = `
          <div class="chat-maps-card-title" style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
            <span>📍 ${v.name}</span>
            ${badge}
          </div>
          <div style="font-size: 0.75rem; color: #FBBF24;">★ ${v.rating} <span style="color:var(--text-muted);">(${v.user_ratings_total || 50}+)</span> • <span style="color:var(--accent-cyan);">${v.category || 'Fitness'}</span></div>
          <div style="font-size: 0.75rem; color: var(--text-secondary);">${v.formatted_address || v.address}</div>
          <div class="chat-maps-links">
            <a href="${v.google_maps_url}" target="_blank" rel="noopener noreferrer">View on Google Maps ↗</a>
            <span>•</span>
            <a href="${v.directions_url}" target="_blank" rel="noopener noreferrer">Get Directions ↗</a>
          </div>
        `;
        mapsWrapper.appendChild(miniCard);
      });
      bubble.appendChild(mapsWrapper);
    }

    msgDiv.appendChild(bubble);
    if (toolsHtml) {
      const toolsDiv = document.createElement("div");
      toolsDiv.innerHTML = toolsHtml;
      msgDiv.appendChild(toolsDiv);
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function sendChatMessage(message) {
    if (!message || !message.trim()) return;
    appendChatMessage("user", message);
    chatInput.value = "";

    try {
      const res = await fetch("/api/v1/coach/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: currentUserId,
          message: message
        })
      });
      const data = await res.json();
      const isSafety = Boolean(data.safety_warning);

      appendChatMessage(
        "coach",
        data.reply,
        data.executed_tools,
        isSafety,
        data.a2ui_messages,
        data.maps_data
      );

      if (isSafety) {
        showToast("🚨 Safety halt triggered: consult a medical professional", "error");
      }

      // If maps data was returned, also sync it into tab-maps
      if (data.maps_data && data.maps_data.venues && mapsVenuesContainer) {
        renderVenueCards(data.maps_data.venues, mapsVenuesContainer);
      }

      // If tools created a plan or updated profile, auto-sync
      if (data.executed_tools && data.executed_tools.some(t => t.tool === "create_workout_plan")) {
        loadActivePlan();
      }
      if (data.executed_tools && data.executed_tools.some(t => t.tool === "update_fitness_profile")) {
        loadProfile();
      }
    } catch (err) {
      appendChatMessage("coach", `⚠️ Communication error: ${err.message}`);
    }
  }

  chatForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    sendChatMessage(chatInput.value);
  });

  // Quick Action Chips
  document.querySelectorAll(".action-chip").forEach(c => {
    c.addEventListener("click", () => {
      sendChatMessage(c.dataset.prompt);
    });
  });

  btnToggleCoachDrawer?.addEventListener("click", () => {
    coachChatDrawer?.scrollIntoView({ behavior: "smooth" });
    chatInput?.focus();
  });

  // ==========================================================================
  // INITIAL BOOTSTRAP
  // ==========================================================================
  checkHealth();
  fetchAthletes().then(() => {
    loadProfile();
    loadActivePlan();
    loadProgress();
  });
  loadExerciseCatalog().then(() => {
    addExerciseToLogUi("ex_dumbbell_bench_press");
  });
});
