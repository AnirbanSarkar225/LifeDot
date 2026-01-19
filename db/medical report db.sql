CREATE TABLE medical_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES userinfo(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE medical_reports
ADD COLUMN description TEXT;
