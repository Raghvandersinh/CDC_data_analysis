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
) TO 'analysis/diabetes_indicator_analysis/data/true_number_estimate.csv' (HEADER, DELIMITER ',');

COPY(
SELECT unit, year, indicator, topic, population, age, race, sex, education, other_info,
CASE
    WHEN (sex = 'All' and education = 'All' and race = 'All') THEN 'All_Population'
    Else NULL
END AS all_pop
FROM di_db.diabetes_ind
WHERE unit LIKE '%Percentage%' and estimate is Not Null and topic = 'Risk Factors for Complications'
) TO 'analysis/diabetes_indicator_analysis/data/Risk_Factor_Percentage.csv' (HEADER, DELIMITER ',');

