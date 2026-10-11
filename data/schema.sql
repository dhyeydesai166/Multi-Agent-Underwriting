CREATE TABLE IF NOT EXISTS applicants (
    applicant_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    occupation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
    applicant_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    amount_usd INTEGER NOT NULL,
    FOREIGN KEY (applicant_id) REFERENCES applicants (applicant_id)
);

CREATE TABLE IF NOT EXISTS policies (
    applicant_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'lapsed')),
    year INTEGER NOT NULL,
    FOREIGN KEY (applicant_id) REFERENCES applicants (applicant_id)
);

CREATE TABLE IF NOT EXISTS applications (
    applicant_id TEXT NOT NULL,
    age INTEGER NOT NULL,
    coverage_amount INTEGER NOT NULL,
    risk_score REAL,
    decision TEXT NOT NULL,
    year INTEGER NOT NULL,
    FOREIGN KEY (applicant_id) REFERENCES applicants (applicant_id)
);
