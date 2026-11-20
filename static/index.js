async function load() {
  const response = await fetch("/api/reservations");
  const data = await response.json();
  render(data);
}

function formatDate(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function render(entries) {
  const root = document.getElementById("container");
  root.innerHTML = "";

  for (let i = 0; i < 90; i++) {
    const d = new Date();
    d.setDate(d.getDate() + i);

    const key = formatDate(d);
    const entry = entries[key];

    const div = document.createElement("div");
    div.className = "day";

    if (d.getDay() === 0 || d.getDay() === 6) {
      div.classList.add("weekend");
    }

    const title = d.toLocaleDateString("de-DE", {
      weekday: "long",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });

    if (!entry) {
      div.innerHTML = `
        <b>${title}</b>
        <br>
        <span class="free">Frei</span>
        <br><br>
        <input id="i-${key}" placeholder="Name">
        <button onclick="reserve('${key}')">
          Reservieren
        </button>
      `;
    } else {
      div.innerHTML = `
        <b>${title}</b>
        <br>
        <span class="used">
          Reserviert von <b class=name></b>
        </span>
        <br><br>
        ${
          entry.editable? `
            <button onclick="removeEntry('${key}')">
              Löschen
            </button>
            `
            : ""
        }
      `;
      div.querySelector(".name").textContent = entry.name;  
    }

    root.appendChild(div);
  }
}

async function reserve(day) {
  const name = document.getElementById(`i-${day}`).value.trim();

  if (!name) {
    alert("Bitte Namen eingeben");
    return;
  }

  try {
    const response = await fetch("/api/reservation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        day: day,
        name: name,
      }),
    });

    if (!response.ok) {
      let message = "Unbekannter Fehler";

      try {
        const data = await response.json()
        message = data.message || message;
      } catch {

      }

      alert(message)
    }
  } catch {
    alert("Server nicht erreichbar.")
  }

  load();
}

async function removeEntry(day) {
  try {
    const response = await fetch(
      "/api/reservation", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ day: day })
      }
    );

    if (!response.ok) {
      alert("Löschen fehlgeschlagen");
    }
  } catch {
    alert("Server nicht erreichbar");
  }

  load();
}

load();
