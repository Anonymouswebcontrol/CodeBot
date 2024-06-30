const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.send('Bot Discord actif et en ligne sur Glitch !');
});

app.listen(port, () => {
    console.log(`Le serveur écoute sur le port ${port}`);
});
