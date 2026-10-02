"use strict";

let jobs = [];
let selectedPriority = "all";
const byId = (id) => document.getElementById(id);
const dateFormat = new Intl.DateTimeFormat(undefined, {
  month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
});

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
    card.querySelector(".job").classList.add(job.priority);
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
  byId("notice").hidden = visible.length > 0;
  byId("notice").textContent = jobs.length ? "No jobs match your filters. Try another search or priority." : "No service jobs yet.";
}

async function loadJobs() {
  byId("refresh").disabled = true;
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
loadJobs();
