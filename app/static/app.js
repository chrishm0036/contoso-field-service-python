"use strict";

// Loads, filters, renders, and completes jobs from the dashboard.

let jobs = [];
let selectedPriority = "all";
const byId = (id) => document.getElementById(id);
const dateFormat = new Intl.DateTimeFormat(undefined, {
  month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
});

// Rebuild the metrics and cards from the latest local job state.
function render() {
  const openJobs = jobs.filter((job) => job.status === "open");
  byId("open-count").textContent = openJobs.length;
  byId("priority-count").textContent = openJobs.filter((job) => ["critical", "high"].includes(job.priority)).length;
  byId("technician-count").textContent = new Set(openJobs.map((job) => job.technician).filter((name) => name !== "Unassigned")).size;
  byId("completed-count").textContent = jobs.filter((job) => job.status === "completed").length;
  byId("total-count").textContent = jobs.length;
  const query = byId("search").value.trim().toLowerCase();
  const visible = jobs.filter((job) =>
    (selectedPriority === "all" || job.priority === selectedPriority) &&
    [`JOB-${String(job.id).padStart(4, "0")}`, job.customer_name, job.description, job.location, job.technician]
      .some((value) => value.toLowerCase().includes(query))
  );
  const fragment = document.createDocumentFragment();
  visible.forEach((job) => {
    const card = byId("job-template").content.cloneNode(true);
    const set = (selector, value) => { card.querySelector(selector).textContent = value; };
    set(".job-id", `JOB-${String(job.id).padStart(4, "0")}`);
    set(".customer", job.customer_name);
    set(".description", job.description);
    set(".location", job.location);
    set(".technician", job.technician);
    set(".priority", job.priority.charAt(0).toUpperCase() + job.priority.slice(1));
    card.querySelector(".priority").classList.add(job.priority);
    const time = card.querySelector("time");
    time.dateTime = job.created_at;
    time.textContent = dateFormat.format(new Date(job.created_at));
    const status = card.querySelector(".status");
    status.classList.toggle("completed", job.status === "completed");
    status.querySelector(".status-label").textContent = job.status === "completed" ? "Completed" : "Open";
    const completeButton = card.querySelector(".complete-job");
    completeButton.dataset.jobId = job.id;
    completeButton.disabled = job.status === "completed";
    completeButton.textContent = job.status === "completed" ? "Completed" : "Complete";
    fragment.appendChild(card);
  });
  byId("jobs").replaceChildren(fragment);
  byId("results").textContent = `Showing ${visible.length} of ${jobs.length} jobs`;
  byId("notice").hidden = visible.length > 0;
  byId("notice").textContent = jobs.length ? "No jobs match your filters. Try another search or priority." : "No service jobs yet.";
}

function setJobActionsBusy(isBusy) {
  document.querySelectorAll(".complete-job").forEach((button) => {
    if (button.textContent !== "Completed") button.disabled = isBusy;
  });
}

// Refresh all jobs while preserving the previous view if the request fails.
async function loadJobs() {
  byId("refresh").disabled = true;
  setJobActionsBusy(true);
  byId("connection").textContent = "Connecting";
  try {
    const response = await fetch("/jobs", { cache: "no-store" });
    if (!response.ok) throw new Error("Could not load jobs");
    jobs = await response.json();
    render();
    byId("connection").textContent = "Operations Live";
  } catch (error) {
    byId("connection").textContent = "Connection unavailable";
    byId("notice").hidden = false;
    byId("notice").textContent = "Unable to refresh service jobs. Check your connection and try Refresh.";
    byId("results").textContent = jobs.length ? "Showing previously loaded jobs" : "Jobs unavailable";
  } finally {
    byId("refresh").disabled = false;
    setJobActionsBusy(false);
  }
}

// Complete one job and replace its local snapshot with the API response.
async function completeJob(jobId, button) {
  button.disabled = true;
  button.textContent = "Completing…";
  byId("refresh").disabled = true;
  byId("action-status").textContent = "";
  try {
    const response = await fetch(`/jobs/${jobId}/complete`, { method: "PATCH" });
    if (!response.ok) throw new Error("Could not complete job");
    const completedJob = await response.json();
    jobs = jobs.map((job) => job.id === completedJob.id ? completedJob : job);
    render();
    byId("action-status").textContent = `JOB-${String(jobId).padStart(4, "0")} completed.`;
    document.querySelector(`.complete-job[data-job-id="${jobId}"]`).closest(".job").querySelector(".status").focus();
  } catch (error) {
    button.disabled = false;
    button.textContent = "Complete";
    byId("notice").hidden = false;
    byId("notice").textContent = "Unable to complete this job. Try again.";
  } finally {
    byId("refresh").disabled = false;
  }
}

document.querySelectorAll("[data-priority]").forEach((button) => {
  button.addEventListener("click", () => {
    selectedPriority = button.dataset.priority;
    document.querySelectorAll("[data-priority]").forEach((item) => {
      item.setAttribute("aria-pressed", String(item === button));
    });
    render();
  });
});
byId("search").addEventListener("input", render);
byId("refresh").addEventListener("click", loadJobs);
byId("jobs").addEventListener("click", (event) => {
  const button = event.target.closest(".complete-job");
  if (button && !button.disabled) completeJob(Number(button.dataset.jobId), button);
});
loadJobs();
