let currentDoctorId = null;
let weekStart = startOfWeek(new Date());
let selectedSlot = null;

const doctorSelect = document.getElementById("doctor-select");
const patientSelect = document.getElementById("patient-select");
const weekGrid = document.getElementById("week-grid");
const weekLabel = document.getElementById("week-label");
const modal = document.getElementById("booking-modal");
const modalSlotLabel = document.getElementById("modal-slot-label");
const modalError = document.getElementById("modal-error");

function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay(); // 0 = Sunday ... 6 = Saturday
  const diff = day === 0 ? 6 : day - 1; // how many days since Monday
  d.setDate(d.getDate() - diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function formatDate(date) {
  return date.toISOString().split("T")[0]; // e.g. "2026-08-10"
}

async function loadDoctors() {
  const res = await fetch("/doctors");
  const doctors = await res.json();
  doctorSelect.innerHTML = doctors
    .map((d) => `<option value="${d.id}">${d.name} — ${d.specialty || "General"}</option>`)
    .join("");
  currentDoctorId = doctors[0]?.id || null;
}

async function loadPatients() {
  const res = await fetch("/patients");
  const patients = await res.json();
  patientSelect.innerHTML = patients
    .map((p) => `<option value="${p.id}">${p.name}</option>`)
    .join("");
}

async function loadWeek() {
  weekGrid.innerHTML = "";
  const days = [0, 1, 2, 3, 4].map((offset) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + offset);
    return d;
  });

  weekLabel.textContent = `${formatDate(days[0])} — ${formatDate(days[4])}`;

  for (const day of days) {
    const column = document.createElement("div");
    column.className = "day-column";

    const header = document.createElement("div");
    header.className = "day-header";
    header.innerHTML = `${day.toLocaleDateString(undefined, { weekday: "long" })}<span class="date">${formatDate(day)}</span>`;
    column.appendChild(header);

    if (currentDoctorId) {
      const res = await fetch(`/doctors/${currentDoctorId}/availability?date=${formatDate(day)}`);
      const data = await res.json();

      if (data.available_slots.length === 0) {
        const note = document.createElement("p");
        note.className = "empty-note";
        note.textContent = "No open slots";
        column.appendChild(note);
      } else {
        data.available_slots.forEach((time) => {
          const pill = document.createElement("button");
          pill.className = "slot-pill";
          pill.textContent = time;
          pill.addEventListener("click", () => openBookingModal(day, time));
          column.appendChild(pill);
        });
      }
    }

    weekGrid.appendChild(column);
  }
}

function openBookingModal(day, time) {
  selectedSlot = { day, time };
  modalSlotLabel.textContent = `${day.toLocaleDateString(undefined, { weekday: "long" })} ${formatDate(day)} at ${time}`;
  modalError.classList.add("hidden");
  modal.classList.remove("hidden");
}

function closeModal() {
  modal.classList.add("hidden");
  selectedSlot = null;
}

async function confirmBooking() {
  const patientId = patientSelect.value;
  const isoLocal = `${formatDate(selectedSlot.day)}T${selectedSlot.time}:00`;

  const res = await fetch("/appointments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      doctor_id: currentDoctorId,
      patient_id: patientId,
      start_time: isoLocal,
    }),
  });

  if (res.ok) {
    closeModal();
    loadWeek();
  } else {
    const err = await res.json();
    modalError.textContent = err.detail || "Booking failed";
    modalError.classList.remove("hidden");
  }
}

document.getElementById("modal-cancel").addEventListener("click", closeModal);
document.getElementById("modal-confirm").addEventListener("click", confirmBooking);
doctorSelect.addEventListener("change", (e) => {
  currentDoctorId = e.target.value;
  loadWeek();
});
document.getElementById("prev-week").addEventListener("click", () => {
  weekStart.setDate(weekStart.getDate() - 7);
  loadWeek();
});
document.getElementById("next-week").addEventListener("click", () => {
  weekStart.setDate(weekStart.getDate() + 7);
  loadWeek();
});

(async function init() {
  await loadDoctors();
  await loadPatients();
  await loadWeek();
})();