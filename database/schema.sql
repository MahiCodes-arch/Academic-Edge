PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS subjects (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, attendance_total INTEGER NOT NULL DEFAULT 0 CHECK(attendance_total >= 0), attendance_present INTEGER NOT NULL DEFAULT 0 CHECK(attendance_present >= 0 AND attendance_present <= attendance_total), exam_date TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chapters (
 id INTEGER PRIMARY KEY, subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE, title TEXT NOT NULL, is_complete INTEGER NOT NULL DEFAULT 0 CHECK(is_complete IN (0,1)), UNIQUE(subject_id,title)
);
CREATE TABLE IF NOT EXISTS study_logs (
 id INTEGER PRIMARY KEY, study_date TEXT NOT NULL, subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL, hours REAL NOT NULL CHECK(hours > 0 AND hours <= 24), notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
