async function fetchAngles() {
    try {
        const res = await fetch('/angles');
        if (!res.ok) return;
        const data = await res.json();
        for (const key in data) {
            document.getElementById('angle-' + key).textContent = data[key];
        }
    } catch (e) {}
}
setInterval(fetchAngles, 1000);
window.addEventListener('DOMContentLoaded', fetchAngles);
