async function load(){

    const response =
        await fetch(
            "/api/reservations"
        );

    const data =
        await response.json();

    render(data);
}


function formatDate(date){

    return date
        .toISOString()
        .split("T")[0];
}


function render(entries){

    const root =
        document.getElementById(
            "container"
        );

    root.innerHTML = "";

    for(let i=0;i<90;i++){

        const d = new Date();

        d.setDate(
            d.getDate()+i
        );

        const key =
            formatDate(d);

        const entry =
            entries[key];

        const div =
            document.createElement(
                "div"
            );

        div.className = "day";

        if(
            d.getDay()===0 ||
            d.getDay()===6
        ){
            div.classList.add(
                "weekend"
            );
        }

        const title =
            d.toLocaleDateString(
                "de-DE",
                {
                    weekday:"long",
                    day:"2-digit",
                    month:"2-digit",
                    year:"numeric"
                }
            );

        if(!entry){

            div.innerHTML = `
                <b>${title}</b>
                <br>
                <span class="free">
                    Frei
                </span>
                <br><br>

                <input
                    id="i-${key}"
                    placeholder="Name">

                <button
                    onclick="reserve('${key}')">
                    Reservieren
                </button>
            `;

        }else{

            div.innerHTML = `
                <b>${title}</b>
                <br>

                <span class="used">
                    Reserviert von
                    <b>${entry.name}</b>
                </span>

                <br><br>

                ${
                    entry.editable
                    ?
                    `<button onclick="removeEntry('${key}')">
                        Löschen
                    </button>`
                    :
                    ""
                }
            `;
        }

        root.appendChild(div);
    }
}


async function reserve(day){

    const name =
        document
        .getElementById(
            `i-${day}`
        )
        .value
        .trim();

    if(!name){

        alert(
            "Bitte Namen eingeben"
        );

        return;
    }

    const response =
        await fetch(
            "/api/reserve",
            {
                method:"POST",

                headers:{
                    "Content-Type":
                    "application/json"
                },

                body:JSON.stringify({

                    day:day,
                    name:name

                })
            }
        );

    if(!response.ok){

        alert(
            "Der Tag ist bereits reserviert."
        );
    }

    load();
}


async function removeEntry(day){

    await fetch(
        "/api/delete",
        {

            method:"POST",

            headers:{
                "Content-Type":
                "application/json"
            },

            body:JSON.stringify({

                day:day

            })
        }
    );

    load();
}


load();