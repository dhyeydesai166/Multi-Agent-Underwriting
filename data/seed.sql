INSERT INTO applicants (applicant_id, full_name, occupation) VALUES
    ('APP-1001', 'Ada Lovelace', 'pilot'),
    ('APP-1002', 'Grace Hopper', 'teacher'),
    ('APP-1003', 'Alan Turing', 'teacher'),
    ('APP-1004', 'Katherine Johnson', 'office worker'),
    ('APP-1005', 'Margaret Hamilton', 'roofer'),
    ('APP-1006', 'Dorothy Vaughan', 'nurse'),
    ('APP-1007', 'Mary Jackson', 'teacher');

INSERT INTO claims (applicant_id, year, amount_usd) VALUES
    ('APP-1002', 2019, 12000),
    ('APP-1005', 2021, 8000),
    ('APP-1006', 2018, 4000);

INSERT INTO policies (applicant_id, status, year) VALUES
    ('APP-1001', 'active', 2024),
    ('APP-1002', 'active', 2024),
    ('APP-1003', 'lapsed', 2023),
    ('APP-1004', 'active', 2024),
    ('APP-1005', 'active', 2024),
    ('APP-1006', 'lapsed', 2022),
    ('APP-1007', 'active', 2024);
