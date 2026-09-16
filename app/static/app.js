"use strict";

let jobs = [];
let selectedPriority = "all";
const byId = (id) => document.getElementById(id);
const dateFormat = new Intl.DateTimeFormat(undefined, {
  month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
});

function setNotice(title, body, showClearFilters) {
  byId("notice").hidden = false;
  byId("notice-announcement").textContent = `${title}. ${body}`;
  byId("notice-title").textContent = title;
  byId("notice-body").textContent = body;
  byId("clear-filters").hidden = !showClearFilters;
}

function render() {
  const openJobs = jobs.filter((job) => job.status === "open");
  byId("open-count").textContent = openJobs.length;
  byId("priority-count").textContent = openJobs.filter((job) => ["critical", "high"].includes(job.priority)).length;
  byId("technician-count").textContent = new Set(openJobs.map((job) => job.technician).filter((name) => name !== "Unassigned")).size;
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
    fragment.appendChild(card);
  });
  byId("jobs").replaceChildren(fragment);
  byId("results").textContent = `Showing ${visible.length} of ${jobs.length} jobs`;
  if (visible.length > 0) {
    byId("notice").hidden = true;
    return;
  }

  if (jobs.length === 0) {
    setNotice("No service jobs yet", "New incidents will appear here after they are created.", false);
    return;
  }

  setNotice("No jobs match these filters", "Try another search or clear the current filters to see every service job again.", true);
}

async function loadJobs() {
  byId("refresh").disabled = true;
  byId("connection").textContent = "Connecting";
  setNotice("Loading service jobs…", "Please wait while the dashboard refreshes.", false);
  try {
    const response = await fetch("/jobs", { cache: "no-store" });
    if (!response.ok) throw new Error("Could not load jobs");
    jobs = await response.json();
    render();
    byId("connection").textContent = "Operations Live";
  } catch (error) {
    byId("connection").textContent = "Connection unavailable";
    setNotice("Unable to refresh service jobs", "Check your connection and try Refresh.", false);
    byId("results").textContent = jobs.length ? "Showing previously loaded jobs" : "Jobs unavailable";
  } finally {
    byId("refresh").disabled = false;
  }
}

function clearFilters() {
  selectedPriority = "all";
  byId("search").value = "";
  document.querySelectorAll("[data-priority]").forEach((item) => {
    item.setAttribute("aria-pressed", String(item.dataset.priority === "all"));
  });
  render();
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
byId("clear-filters").addEventListener("click", () => {
  clearFilters();
  byId("search").focus();
});
loadJobs();
