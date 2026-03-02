import sqlite3

def init_db():
    conn = sqlite3.connect('stewardship.db')
    c = conn.cursor()

    # Drop existing tables
    c.execute("DROP TABLE IF EXISTS drugs")
    c.execute("DROP TABLE IF EXISTS antibiograms")
    c.execute("DROP TABLE IF EXISTS global_guidelines")
    c.execute("DROP TABLE IF EXISTS disease_drug_lines")
    c.execute("DROP TABLE IF EXISTS patients")

    # 1. Drugs Table
    c.execute('''CREATE TABLE drugs (
        id INTEGER PRIMARY KEY,
        name TEXT,
        class TEXT,
        aware_category TEXT,
        spectrum TEXT,
        pregnancy_safe INTEGER,
        renal_adjustment_needed INTEGER,
        standard_dose TEXT,
        duration TEXT,
        renal_dose_adjustment TEXT,
        hepatic_dose_adjustment TEXT
    )''')

    # 2. Antibiograms Table
    c.execute('''CREATE TABLE antibiograms (
        id INTEGER PRIMARY KEY,
        microorganism TEXT,
        drug_name TEXT,
        location TEXT,
        sensitivity_percent REAL
    )''')

    # 3. Global Guidelines
    c.execute('''CREATE TABLE global_guidelines (
        id INTEGER PRIMARY KEY,
        disease_keyword TEXT,
        recommended_drug TEXT,
        rationale TEXT
    )''')

    # 4. Disease-Drug Lines
    c.execute('''CREATE TABLE disease_drug_lines (
        id INTEGER PRIMARY KEY,
        disease_keyword TEXT,
        drug_name TEXT,
        line INTEGER,
        source TEXT
    )''')

    # 5. Patients Table
    c.execute('''CREATE TABLE patients (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        disease TEXT,
        microorganism TEXT,
        location TEXT,
        age INTEGER,
        sex TEXT,
        pregnancy BOOLEAN,
        allergy TEXT,
        crcl REAL,
        lfts TEXT,
        recommended_drug TEXT,
        dose TEXT,
        sensitivity TEXT,
        aware TEXT,
        rationale TEXT
    )''')

    # ---------- Insert Drugs (expanded list) ----------
    drugs_data = [
        # UTI drugs
        ('Nitrofurantoin', 'Nitrofuran', 'Access', 'Narrow', 1, 1,
         '100 mg BD', '5 days', 'Avoid if CrCl < 30', 'No adjustment needed'),
        ('Fosfomycin', 'Phosphonic Acid', 'Access', 'Narrow', 1, 0,
         '3 g single dose', '1 day', 'No adjustment needed', 'No adjustment needed'),
        ('Ciprofloxacin', 'Fluoroquinolone', 'Watch', 'Broad', 0, 1,
         '500 mg BD', '7 days', 'Reduce dose 50% if CrCl < 30', 'Use caution in liver disease'),
        ('Trimethoprim-Sulfamethoxazole', 'Sulfonamide', 'Access', 'Broad', 0, 1,
         '160/800 mg BD', '7 days', 'Reduce dose if CrCl < 30', 'Avoid in severe liver disease'),
        # Pneumonia drugs
        ('Amoxicillin-Clavulanate', 'Penicillin', 'Access', 'Broad', 1, 1,
         '875 mg BD', '7 days', 'Reduce dose if CrCl < 30', 'No adjustment needed'),
        ('Azithromycin', 'Macrolide', 'Access', 'Broad', 1, 0,
         '500 mg once, then 250 mg daily', '5 days', 'No adjustment needed', 'Use caution in severe liver disease'),
        ('Doxycycline', 'Tetracycline', 'Access', 'Broad', 0, 0,
         '100 mg BD', '7 days', 'No adjustment needed', 'No adjustment needed'),
        ('Levofloxacin', 'Fluoroquinolone', 'Watch', 'Broad', 0, 1,
         '750 mg daily', '5 days', 'Reduce dose if CrCl < 30', 'No adjustment needed'),
        ('Ceftriaxone', 'Cephalosporin', 'Watch', 'Broad', 1, 0,
         '1 g daily', '7 days', 'No adjustment needed', 'No adjustment needed'),
        # Typhoid drugs
        ('Azithromycin', 'Macrolide', 'Access', 'Broad', 1, 0,
         '500 mg once, then 250 mg daily', '5 days', 'No adjustment needed', 'Use caution in severe liver disease'),
        ('Ceftriaxone', 'Cephalosporin', 'Watch', 'Broad', 1, 0,
         '1 g daily', '7 days', 'No adjustment needed', 'No adjustment needed'),
        ('Ciprofloxacin', 'Fluoroquinolone', 'Watch', 'Broad', 0, 1,
         '500 mg BD', '7 days', 'Reduce dose 50% if CrCl < 30', 'Use caution in liver disease'),
        # Skin abscess drugs
        ('Cefalexin', 'Cephalosporin', 'Access', 'Narrow', 1, 1,
         '500 mg QD', '7 days', 'Reduce dose if CrCl < 30', 'No adjustment needed'),
        ('Clindamycin', 'Lincosamide', 'Access', 'Narrow', 1, 0,
         '300 mg QD', '7 days', 'No adjustment needed', 'Reduce in severe liver disease'),
        ('Doxycycline', 'Tetracycline', 'Access', 'Broad', 0, 0,
         '100 mg BD', '7 days', 'No adjustment needed', 'No adjustment needed'),
        ('Linezolid', 'Oxazolidinone', 'Reserve', 'Narrow', 1, 0,
         '600 mg BD', '10 days', 'No adjustment needed', 'No adjustment needed'),
        # Additional drugs to reach 25+
        ('Gentamicin', 'Aminoglycoside', 'Access', 'Broad', 0, 1,
         '5 mg/kg daily', '7 days', 'Adjust dose based on levels', 'No adjustment needed'),
        ('Vancomycin', 'Glycopeptide', 'Reserve', 'Broad', 1, 1,
         '15 mg/kg BD', '7 days', 'Adjust based on levels', 'No adjustment needed'),
        ('Meropenem', 'Carbapenem', 'Reserve', 'Broad', 1, 1,
         '1 g TID', '7 days', 'Reduce dose 50% if CrCl < 30', 'No adjustment needed'),
        ('Piperacillin-Tazobactam', 'Penicillin', 'Reserve', 'Broad', 1, 1,
         '4.5 g QD', '7 days', 'Adjust dose if CrCl < 30', 'No adjustment needed'),
    ]
    c.executemany('''INSERT INTO drugs VALUES (NULL,?,?,?,?,?,?,?,?,?,?)''', drugs_data)

    # ---------- Antibiogram Data for 4 diseases in Guntur and Delhi ----------
    # Microorganisms: E. Coli (UTI), S. Pneumoniae (Pneumonia), S. Typhi (Typhoid), S. Aureus (Skin abscess)
    antibiogram_data = [
        # UTI (E. Coli) - Guntur
        ('E. Coli', 'Nitrofurantoin', 'Guntur', 82.0),
        ('E. Coli', 'Fosfomycin', 'Guntur', 90.0),
        ('E. Coli', 'Ciprofloxacin', 'Guntur', 45.0),
        ('E. Coli', 'Trimethoprim-Sulfamethoxazole', 'Guntur', 68.0),
        # UTI (E. Coli) - Delhi (different sensitivity so Fosfomycin remains top but with different secondary)
        ('E. Coli', 'Nitrofurantoin', 'Delhi', 70.0),
        ('E. Coli', 'Fosfomycin', 'Delhi', 88.0),
        ('E. Coli', 'Ciprofloxacin', 'Delhi', 60.0),
        ('E. Coli', 'Trimethoprim-Sulfamethoxazole', 'Delhi', 55.0),

        # Pneumonia (S. Pneumoniae) - Guntur (Amoxicillin-Clavulanate top)
        ('S. Pneumoniae', 'Amoxicillin-Clavulanate', 'Guntur', 85.0),
        ('S. Pneumoniae', 'Azithromycin', 'Guntur', 78.0),
        ('S. Pneumoniae', 'Doxycycline', 'Guntur', 72.0),
        ('S. Pneumoniae', 'Levofloxacin', 'Guntur', 68.0),
        # Pneumonia (S. Pneumoniae) - Delhi (Azithromycin top)
        ('S. Pneumoniae', 'Amoxicillin-Clavulanate', 'Delhi', 70.0),
        ('S. Pneumoniae', 'Azithromycin', 'Delhi', 88.0),
        ('S. Pneumoniae', 'Doxycycline', 'Delhi', 75.0),
        ('S. Pneumoniae', 'Levofloxacin', 'Delhi', 65.0),

        # Typhoid (S. Typhi) - Guntur (Azithromycin top)
        ('S. Typhi', 'Azithromycin', 'Guntur', 92.0),
        ('S. Typhi', 'Ceftriaxone', 'Guntur', 88.0),
        ('S. Typhi', 'Ciprofloxacin', 'Guntur', 50.0),
        # Typhoid (S. Typhi) - Delhi (Ceftriaxone top)
        ('S. Typhi', 'Azithromycin', 'Delhi', 78.0),
        ('S. Typhi', 'Ceftriaxone', 'Delhi', 94.0),
        ('S. Typhi', 'Ciprofloxacin', 'Delhi', 45.0),

        # Skin abscess (S. Aureus) - Guntur (Cefalexin top)
        ('S. Aureus', 'Cefalexin', 'Guntur', 86.0),
        ('S. Aureus', 'Clindamycin', 'Guntur', 80.0),
        ('S. Aureus', 'Doxycycline', 'Guntur', 75.0),
        ('S. Aureus', 'Linezolid', 'Guntur', 98.0),
        # Skin abscess (S. Aureus) - Delhi (Clindamycin top)
        ('S. Aureus', 'Cefalexin', 'Delhi', 70.0),
        ('S. Aureus', 'Clindamycin', 'Delhi', 89.0),
        ('S. Aureus', 'Doxycycline', 'Delhi', 82.0),
        ('S. Aureus', 'Linezolid', 'Delhi', 99.0),
    ]
    c.executemany('INSERT INTO antibiograms VALUES (NULL,?,?,?,?)', antibiogram_data)

    # ---------- Global Guidelines (first‑line) ----------
    guideline_data = [
        ('UTI', 'Nitrofurantoin', 'First-line for Uncomplicated Cystitis'),
        ('UTI', 'Fosfomycin', 'Alternative for UTI'),
        ('Pneumonia', 'Amoxicillin-Clavulanate', 'First-line for Community Acquired Pneumonia'),
        ('Pneumonia', 'Azithromycin', 'First-line for atypical coverage'),
        ('Typhoid', 'Azithromycin', 'First-line per ICMR for Enteric Fever'),
        ('Typhoid', 'Ceftriaxone', 'Alternative for severe typhoid'),
        ('Skin abscess', 'Cefalexin', 'First-line for mild skin infections'),
        ('Skin abscess', 'Clindamycin', 'Second-line for skin/soft tissue'),
    ]
    c.executemany('INSERT INTO global_guidelines VALUES (NULL,?,?,?)', guideline_data)

    # ---------- Disease‑Drug Lines ----------
    lines_data = [
        ('UTI', 'Nitrofurantoin', 1, 'IDSA'),
        ('UTI', 'Fosfomycin', 2, 'IDSA'),
        ('UTI', 'Trimethoprim-Sulfamethoxazole', 2, 'IDSA'),
        ('UTI', 'Ciprofloxacin', 3, 'IDSA'),
        ('Pneumonia', 'Amoxicillin-Clavulanate', 1, 'ATS'),
        ('Pneumonia', 'Azithromycin', 1, 'ATS'),
        ('Pneumonia', 'Doxycycline', 2, 'ATS'),
        ('Pneumonia', 'Levofloxacin', 2, 'ATS'),
        ('Typhoid', 'Azithromycin', 1, 'ICMR'),
        ('Typhoid', 'Ceftriaxone', 2, 'ICMR'),
        ('Typhoid', 'Ciprofloxacin', 3, 'ICMR'),
        ('Skin abscess', 'Cefalexin', 1, 'IDSA'),
        ('Skin abscess', 'Clindamycin', 2, 'IDSA'),
        ('Skin abscess', 'Doxycycline', 2, 'IDSA'),
        ('Skin abscess', 'Linezolid', 3, 'IDSA'),
    ]
    c.executemany('INSERT INTO disease_drug_lines VALUES (NULL,?,?,?,?)', lines_data)

    conn.commit()
    conn.close()
    print("✅ Database initialized with 4 diseases, Guntur & Delhi locations, and at least 4 drugs per disease/location.")

if __name__ == "__main__":
    init_db()