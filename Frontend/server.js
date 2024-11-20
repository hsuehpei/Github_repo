import express from 'express';

const app = express();
const port = 4000;

app.use(express.static('dist'));

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
