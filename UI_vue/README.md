USRP X440 UI (Vue)

Quick start:

```bash
cd UI_vue
npm install
npm run dev
```

Backend (Python) server:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The backend exposes these endpoints used by the UI:
- `POST /api/generate` -> body `{ f_min, f_max, time }` (calls processing scripts)
- `POST /api/filters` -> saves filters to `assistanceJSONs/filters.json`
- `GET /api/options` -> returns `assistanceJSONs/filteredOptions.json`

Notes:
- Entry file: UI_vue/src/main.js
- Example App: UI_vue/src/App.vue
- Input component: UI_vue/src/components/InputBox.vue (`InputBox`)

You can also use `pnpm` or `yarn` instead of `npm` if preferred.
