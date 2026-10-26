// Aplica o tema salvo antes de a página desenhar (evita piscar o tema escuro).
// Fica num arquivo próprio porque a Content-Security-Policy proíbe script embutido no HTML.
try { document.documentElement.dataset.theme = localStorage.getItem("pp-theme") || "dark"; } catch (e) { /* sem armazenamento */ }
