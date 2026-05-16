## Data Import Plus

A custom Frappe/ERPNext app that adds a **Preview & Fix** workflow to data
imports. Instead of importing a spreadsheet blindly and discovering errors
afterwards, users upload a file, fix problems in an interactive grid, and only
then commit clean data.

### Features

- **"Import with Preview" button** on the list views of Item, Customer and
  Supplier.
- **Pandas-based parsing** of `.xlsx`, `.xls` and `.csv` uploads.
- **Three pre-import checks**
  - Duplicate rows (by a configured unique field).
  - Missing mandatory fields.
  - Invalid Link field values (the referenced record must exist).
- **Editable preview grid** with colour coding:
  - Red row — duplicate entry.
  - Orange cell — missing mandatory value.
  - Yellow cell — invalid link value.
- **In-grid fixes** — inline cell editing with live re-validation, delete/skip
  a row, and one-click "Auto-fix Duplicates" (keeps the first occurrence).
- **Guarded import** — the Import button stays disabled until zero errors
  remain; the server re-validates before inserting.
- **Audit trail** — every run creates a `Data Import Log` with the original
  upload and a generated "cleaned" file attached.

### Usage

1. Open the list view of Item, Customer or Supplier.
2. Click **Import with Preview** and choose a spreadsheet.
3. Fix any highlighted issues in the grid (or use **Auto-fix Duplicates**).
4. When the error count reaches 0, click **Import**.
5. Review the run under **Data Import Log**.

The tool is also available directly at `/app/data-import-plus`.

### Adding more doctypes

Edit `data_import_plus/data_import_plus/doctype_config.py` and add an entry
with the field used to detect duplicates, then add the doctype to the
`SUPPORTED` list in `public/js/import_with_preview.js`.

### Architecture

| Layer | File |
|-------|------|
| List view button | `public/js/import_with_preview.js` |
| Preview & Fix page | `data_import_plus/page/data_import_plus/` |
| Page styling | `public/css/data_import_plus.css` |
| Backend API | `data_import_plus/api.py` |
| Doctype config | `data_import_plus/doctype_config.py` |
| Audit log doctype | `data_import_plus/doctype/data_import_log/` |

### Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench --site $SITE install-app data_import_plus
```

### License

mit
