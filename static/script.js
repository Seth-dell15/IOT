document.getElementById("pairing-form").addEventListener("submit", async function(e) {
    e.preventDefault();
    const code = document.getElementById("pairing-code").value;

    const response = await fetch("/pairing/send", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ code: code })
    });

    console.log("Réponse fetch:", response.status);

    if (response.ok) {
        document.getElementById("pairing-status").innerText = "Code envoyé ✅";
        document.getElementById("pairing-code").value = "";
    } else {
        document.getElementById("pairing-status").innerText = "Erreur ❌";
    }
});


    setInterval(function() {
        location.reload();
    }, 60000); // toutes les 60 secondes

    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onmessage = function(event) {
        if (event.data === "update") {
            location.reload();
        }
    };