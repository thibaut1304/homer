const express = require("express");
const fetch = require("node-fetch");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 8080;
const API_BACKEND_URL = process.env.API_BACKEND_URL || "http://homer-api-backend:8001";

// Sert les fichiers statiques
app.use(express.static(path.join(__dirname)));

// Proxy API
app.get("/server", async (req, res) => {
  const { service, url } = req.query;

  if (!service || !url) {
    return res.status(400).json({ error: "Paramètres manquants." });
  }

  try {
    const apiUrl = `${API_BACKEND_URL}/api-proxy/?service=${encodeURIComponent(service)}&url=${encodeURIComponent(url)}`;

    // Transfert des headers originaux (Authorization, etc.)
    const proxyHeaders = {
      ...req.headers,
      host: undefined, // Important : ne pas passer le host d'origine
    };

    const response = await fetch(apiUrl, {
      method: "GET",
      headers: proxyHeaders,
    });

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const data = await response.json();
      return res.status(response.status).json(data);
    }

    const text = await response.text();
    return res.status(response.status).send(text);
  } catch (err) {
    console.error("Erreur proxy:", err);
    res.status(502).json({ error: "Erreur proxy Homer", details: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`✅ Homer avec backend proxy lancé sur http://localhost:${PORT}`);
});
