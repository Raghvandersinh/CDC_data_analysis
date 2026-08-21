COPY(
    SELECT unit, year, indicator, topic, population, age, race, sex, education, other_info,
    CASE
        WHEN unit = 'Number in 1,000,000s' THEN estimate * 1000000
        WHEN unit = 'Number in 1,000s' THEN estimate * 1000
        WHEN unit = 'Number of Discharges in 1,000s' THEN estimate * 1000
        ELSE estimate
    END as true_number_estimate,
    CASE
        WHEN unit LIKE '%Number%' and unit Like '%Discharges%' THEN 'Discharge'
        ELSE 'Normal'
    END AS unit_category
    FROM di_db.diabetes_ind
    WHERE unit LIKE '%Number%' and estimate is not NULL
    ORDER BY unit ASC
) TO 'true_number_estimate.csv' (HEADER, DELIMITER ',');

